import os
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from shapely import wkt
from shapely.geometry import Point

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

CID_URL = os.getenv("CID_DB_URL")
MON_URL = os.getenv("MONITOREO_DB_URL")
BIL_URL = os.getenv("BILLETAJE_DB_URL")

class UFMetricsCalculator:
    def __init__(self):
        self.engine_cid = create_engine(CID_URL) if CID_URL else None
        self.engine_mon = create_engine(MON_URL) if MON_URL else None
        self.engine_bil = create_engine(BIL_URL) if BIL_URL else None

    def get_uf_structure(self, id_uf=None):
        query = text("""
            SELECT 
                uf.id_uf,
                uf.nombre_uf,
                t.id_troncal,
                t.nombre as troncal_nombre,
                t.es_principal,
                ST_AsText(t.geom) as troncal_geom,
                c.ruta_hex,
                e.id_eot_vmt_hex as agency_id
            FROM gestion_uf.unidades_funcionales uf
            JOIN gestion_uf.uf_troncales t ON uf.id_uf = t.id_uf
            JOIN gestion_uf.composicion_uf c ON uf.id_uf = c.id_uf
            JOIN public.catalogo_rutas r ON c.ruta_hex = r.ruta_hex
            JOIN public.eots e ON r.id_eot_catalogo = e.cod_catalogo
            WHERE (:id_uf IS NULL OR uf.id_uf = :id_uf)
              AND t.activo = TRUE
              AND (c.fecha_fin IS NULL OR c.fecha_fin >= CURRENT_DATE)
        """)
        
        with self.engine_cid.connect() as conn:
            df = pd.read_sql(query, conn, params={"id_uf": id_uf})
            return df

    def get_gps_data(self, agency_ids, route_ids, fecha):
        if not self.engine_mon:
            return pd.DataFrame()

        # Optimizamos la query para traer solo lo necesario
        query = text("""
            SELECT 
                identidad as id_bus,
                route_id as ruta_hex,
                fecha_hora as timestamp,
                latitude as lat,
                longitude as lon
            FROM public.app_monitoreo_mensajeoperativo
            WHERE agency_id IN :agencies
              AND route_id IN :routes
              AND fecha_hora >= :start_ts
              AND fecha_hora < :end_ts
            ORDER BY identidad, fecha_hora ASC
        """)
        
        start_ts = datetime.combine(fecha, datetime.min.time())
        end_ts = start_ts + timedelta(days=1)
        
        with self.engine_mon.connect() as conn:
            df = pd.read_sql(query, conn, params={
                "agencies": tuple(agency_ids),
                "routes": tuple(route_ids),
                "start_ts": start_ts,
                "end_ts": end_ts
            })
            return df

    def get_validations_count(self, id_bus, ruta_hex, timestamp_limit):
        """
        Calcula validaciones en Billetaje. 
        Intenta conectarse, si falla devuelve 0.
        """
        if not self.engine_bil:
            return 0

        query = text("""
            SELECT COUNT(*) as count
            FROM public.c_transacciones
            WHERE v_id = :id_bus
              AND idrutaestacion = :ruta_hex
              AND fechahoraevento >= :start_of_day
              AND fechahoraevento < :limit
        """)
        
        start_of_day = timestamp_limit.replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # Dado que el billetaje suele ser lento o fallar, ponemos un timeout corto
            with self.engine_bil.connect().execution_options(timeout=10) as conn:
                res = conn.execute(query, {
                    "id_bus": str(id_bus),
                    "ruta_hex": ruta_hex,
                    "start_of_day": start_of_day,
                    "limit": timestamp_limit
                }).fetchone()
                return res[0] if res else 0
        except Exception:
            # logger.error(f"Error en Billetaje para bus {id_bus}: {e}")
            return 0

    def run_analysis(self, id_uf, fecha_str):
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        logger.info(f"--- Iniciando análisis UF {id_uf} | Fecha: {fecha} ---")
        
        # 1. Cargar Estructura
        df_struct = self.get_uf_structure(id_uf)
        if df_struct.empty:
            logger.error("No se encontró estructura")
            return
        
        agencies = [a for a in df_struct['agency_id'].unique().tolist() if a]
        routes = [r for r in df_struct['ruta_hex'].unique().tolist() if r]
        
        troncales_df = df_struct[['id_troncal', 'troncal_nombre', 'es_principal', 'troncal_geom']].drop_duplicates()
        troncales_gdf = gpd.GeoDataFrame(
            troncales_df, 
            geometry=troncales_df['troncal_geom'].apply(wkt.loads),
            crs="EPSG:4326"
        )

        # 2. Cargar GPS
        logger.info(f"Consultando GPS en Monitoreo...")
        df_gps = self.get_gps_data(agencies, routes, fecha)
        if df_gps.empty:
            logger.warning("No se obtuvieron datos GPS")
            return
            
        logger.info(f"Obtenidos {len(df_gps)} puntos GPS. Procesando espacialmente...")
        
        # Convertir GPS a GeoDataFrame para procesamiento masivo
        gdf_gps = gpd.GeoDataFrame(
            df_gps,
            geometry=gpd.points_from_xy(df_gps.lon, df_gps.lat),
            crs="EPSG:4326"
        )
        
        # 3. Intersección Espacial (Spatial Join)
        # Esto es MUCHO más rápido que iterar uno por uno
        joined = gpd.sjoin(gdf_gps, troncales_gdf, predicate='within')
        
        if joined.empty:
            logger.warning("Ningún bus entró a las troncales en este día.")
            return

        # 4. Encontrar la PRIMERA entrada a cada troncal por bus/trip
        # (Para este ejercicio asumimos que la primera entrada del día es la que importa, 
        # aunque en producción se haría por vuelta)
        first_entries = joined.sort_values('timestamp').groupby(['id_bus', 'ruta_hex', 'id_troncal']).first().reset_index()
        
        logger.info(f"Detectadas {len(first_entries)} entradas únicas a troncales. Consultando Billetaje...")
        
        # 5. Cruzar con Billetaje
        # Para no saturar, podemos agrupar o hacer batch
        results = []
        for _, row in first_entries.iterrows():
            validaciones = self.get_validations_count(row['id_bus'], row['ruta_hex'], row['timestamp'])
            
            results.append({
                "troncal": row['troncal_nombre'],
                "es_principal": row['es_principal'],
                "hora": row['timestamp'].hour,
                "validaciones": validaciones
            })
            
        df_final = pd.DataFrame(results)
        
        # 6. Agregación y Reporte
        def get_franja(h):
            if 5 <= h < 9: return "05-09 (Pico M)"
            if 9 <= h < 12: return "09-12 (Valle M)"
            if 12 <= h < 15: return "12-15 (Pico MD)"
            if 15 <= h < 19: return "15-19 (Pico T)"
            if 19 <= h < 23: return "19-23 (Valle N)"
            return "23-05 (Nocturno)"

        df_final['franja'] = df_final['hora'].apply(get_franja)
        
        report = df_final.groupby(['troncal', 'es_principal', 'hora', 'franja']).agg({
            'validaciones': ['count', 'sum', 'mean']
        })
        report.columns = ['cantidad_buses', 'total_validaciones', 'promedio_ocupacion']
        report = report.reset_index()
        
        # Ordenar por importancia (Principal primero, luego hora)
        report = report.sort_values(['es_principal', 'hora'], ascending=[False, True])
        
        print("\n" + "="*60)
        print(f"REPORTE DE OCUPACIÓN AL ENTRAR A TRONCALES - UF {id_uf}")
        print("="*60)
        print(report.to_string(index=False))
        
        # Guardar resultados
        output_path = f"reporte_ocupacion_uf{id_uf}_{fecha_str}.csv"
        report.to_csv(output_path, index=False)
        logger.info(f"Reporte exportado a {output_path}")

if __name__ == "__main__":
    import sys
    calc = UFMetricsCalculator()
    uf_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    fecha = sys.argv[2] if len(sys.argv) > 2 else "2024-05-10"
    calc.run_analysis(uf_id, fecha)
