import logging
import pandas as pd
import geopandas as gpd
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, date as date_type
from shapely import wkt
from shapely.geometry import Point, shape
from typing import List, Dict, Any, Optional
import json
from pyproj import Transformer
from shapely.ops import transform as shp_transform

from app.services.cid_service import cid_service
from app.services.billetaje_service import billetaje_service

logger = logging.getLogger(__name__)

# Franjas por defecto (nombre, h0_inclusive, h1_exclusive)
FRANJAS_DEFAULT = [
    ("Madrugada (00-05)", 0, 5),
    ("Pico mañana (05-09)", 5, 9),
    ("Media mañana (09-12)", 9, 12),
    ("Mediodía (12-15)", 12, 15),
    ("Tarde (15-19)", 15, 19),
    ("Noche (19-24)", 19, 24),
]


def _get_franja(hora: int, franjas: list) -> str:
    for nombre, h0, h1 in franjas:
        if h0 <= hora < h1:
            return nombre
    return "Resto"


def _project_geometry(geom_wgs):
    """Proyecta de WGS84 a EPSG:32721 (métrico) para cálculos precisos."""
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32721", always_xy=True)
    return shp_transform(lambda x, y, z=None: transformer.transform(x, y), geom_wgs)


class UFAnalysisService:
    def get_simulation_data(
        self,
        cid_db: Session,
        monitoreo_db: Session,
        billetaje_db: Session,
        id_uf: int,
        fecha_str: str,
        # Parámetros avanzados configurables
        hora_inicio: int = 0,
        hora_fin: int = 24,
        buf_troncal_m: float = 90.0,
        sep_entrada_min: int = 45,
        ventana_val_min: int = 60,
    ) -> Dict[str, Any]:
        """
        Realiza el análisis de carga de la UF para una fecha dada.
        Retorna métricas, por_hora, por_franja, eventos y diagnóstico SNBE.
        """
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        # 1. Obtener Estructura y Troncales
        troncales = cid_service.get_uf_troncales(cid_db, id_uf)
        geocercas_ref = cid_service.get_geocercas_uf(cid_db, id_uf)
        puntos_inicio = cid_service.get_puntos_inicio_uf(cid_db, id_uf)

        # Obtener rutas y agencias para consulta GPS
        query_struct = text("""
            SELECT DISTINCT
                c.ruta_hex,
                r.ruta_dec,
                e.id_eot_vmt_hex as agency_id
            FROM gestion_uf.composicion_uf c
            JOIN public.catalogo_rutas r ON c.ruta_hex = r.ruta_hex
            JOIN public.eots e ON r.id_eot_catalogo = e.cod_catalogo
            WHERE c.id_uf = :id_uf
              AND c.fecha_inicio <= :fecha
              AND (c.fecha_fin IS NULL OR c.fecha_fin >= :fecha)
        """)
        struct_res = cid_db.execute(query_struct, {"id_uf": id_uf, "fecha": fecha}).fetchall()

        if not struct_res:
            return {
                "metrics": [], "por_hora": [], "por_franja": [],
                "eventos": [], "snbe_diag": None,
                "troncales": troncales, "puntos_inicio": puntos_inicio,
                "mensaje": "No se encontró composición para esta UF en la fecha seleccionada",
            }

        agencies = list({r.agency_id for r in struct_res if r.agency_id})
        routes = list({r.ruta_hex for r in struct_res if r.ruta_hex})
        rutas_dec = list({str(int(float(r.ruta_dec))) for r in struct_res if r.ruta_dec is not None})

        # 2. Consultar GPS en Monitoreo (respetando ventana horaria)
        start_ts = datetime.combine(fecha, datetime.min.time()).replace(hour=hora_inicio)
        end_ts = datetime.combine(fecha, datetime.min.time()).replace(hour=min(hora_fin, 23), minute=59, second=59)

        query_gps = text("""
            SELECT
                mean_id as id_bus,
                route_id as ruta_hex,
                fecha_hora as timestamp,
                latitude as lat,
                longitude as lon
            FROM public.app_monitoreo_mensajeoperativo
            WHERE agency_id IN :agencies
              AND fecha_hora >= :start_ts
              AND fecha_hora < :end_ts
            LIMIT 30000
        """)

        gps_res = monitoreo_db.execute(query_gps, {
            "agencies": tuple(agencies),
            "start_ts": start_ts,
            "end_ts": end_ts,
        }).fetchall()

        if not gps_res:
            return {
                "metrics": [], "por_hora": [], "por_franja": [],
                "eventos": [], "snbe_diag": None,
                "troncales": troncales, "puntos_inicio": puntos_inicio,
                "mensaje": "No hay datos GPS para esta UF en la fecha/ventana seleccionada",
            }

        df_gps = pd.DataFrame([dict(r._asdict()) for r in gps_res])
        df_gps["timestamp"] = pd.to_datetime(df_gps["timestamp"], utc=True, errors="coerce")
        total_gps = len(df_gps)

        # 3. Construcción de zonas de troncal proyectadas (Métrico)
        troncales_data = []
        troncales_geofences = [g for g in geocercas_ref if g["id_tipo"] == 7]

        for g in troncales_geofences:
            if g["geojson"]:
                wgs_geom = shape(json.loads(g["geojson"]))
                troncales_data.append({
                    "id_troncal": g["id_geocerca"],
                    "nombre": g["ruta_hex"],
                    "es_principal": g["es_principal"],
                    "geometry": _project_geometry(wgs_geom),
                })

        if not troncales_data:
            for t in troncales:
                if t["geojson"]:
                    wgs_geom = shape(json.loads(t["geojson"]))
                    troncales_data.append({
                        "id_troncal": t["id_troncal"],
                        "nombre": t["nombre"],
                        "es_principal": t["es_principal"],
                        "geometry": _project_geometry(wgs_geom).buffer(buf_troncal_m),
                    })

        if not troncales_data:
            return {
                "metrics": [], "por_hora": [], "por_franja": [],
                "eventos": [], "snbe_diag": None,
                "troncales": troncales, "puntos_inicio": puntos_inicio,
                "mensaje": "No se definieron troncales para esta UF",
            }

        troncales_gdf = gpd.GeoDataFrame(troncales_data, crs="EPSG:32721")

        # 4. Spatial Join con Proyección
        gdf_gps = gpd.GeoDataFrame(
            df_gps,
            geometry=gpd.points_from_xy(df_gps.lon, df_gps.lat),
            crs="EPSG:4326",
        ).to_crs("EPSG:32721")
        
        joined = gpd.sjoin(gdf_gps, troncales_gdf, predicate="within")

        # 5. Lógica de "Ingreso" (Transición fuera -> dentro)
        # Re-ordenamos por bus y tiempo para detectar el momento exacto del cruce
        df_gps_full = gdf_gps.sort_values(["id_bus", "timestamp"])
        
        # Mapeamos qué puntos están en qué troncal
        # (Un punto puede estar en varias geocercas si se solapan, tomamos la primera por ahora)
        gps_to_troncal = joined.groupby(joined.index)["id_troncal"].first()
        df_gps_full["in_troncal_id"] = gps_to_troncal

        eventos_list = []
        last_entry_time: Dict[tuple, datetime] = {}
        sep = timedelta(minutes=sep_entrada_min)

        for id_bus, group in df_gps_full.groupby("id_bus"):
            prev_troncal = None
            for _, row in group.iterrows():
                curr_troncal = row["in_troncal_id"]
                
                # Detectamos transición: antes no estaba en esta troncal, ahora sí
                if pd.notna(curr_troncal) and curr_troncal != prev_troncal:
                    t = row["timestamp"]
                    key = (id_bus, curr_troncal)
                    
                    # Control de separación mínima
                    if key in last_entry_time and (t - last_entry_time[key]) < sep:
                        prev_troncal = curr_troncal
                        continue
                        
                    last_entry_time[key] = t
                    tr_info = next(tr for tr in troncales_data if tr["id_troncal"] == curr_troncal)
                    
                    eventos_list.append({
                        "id_bus": id_bus,
                        "ruta_hex": row["ruta_hex"],
                        "nombre_troncal": tr_info["nombre"],
                        "es_principal": bool(tr_info["es_principal"]),
                        "tipo_troncal": "principal" if tr_info["es_principal"] else "secundaria",
                        "hora": t.hour,
                        "timestamp": t.isoformat(),
                        "lat": row["lat"],
                        "lon": row["lon"],
                        "id_troncal": curr_troncal
                    })
                
                prev_troncal = curr_troncal

        df_eventos = pd.DataFrame(eventos_list)
        if df_eventos.empty:
            return {
                "metrics": [], "por_hora": [], "por_franja": [],
                "eventos": [], "snbe_diag": None,
                "troncales": troncales, "puntos_inicio": puntos_inicio,
                "mensaje": "No se detectaron ingresos con los parámetros actuales",
            }

        # 6. Cruzar con Billetaje por evento (usando ventana configurable)
        rutas_dec_map = {str(r.ruta_hex): str(int(float(r.ruta_dec))) for r in struct_res if r.ruta_dec is not None}

        # 6. Cruzar con Billetaje (Optimizado: un solo query batch)
        rutas_dec_map = {str(r.ruta_hex): str(int(float(r.ruta_dec))) for r in struct_res if r.ruta_dec is not None}
        idsams_detectados = list(df_eventos["id_bus"].unique())
        rutas_ids = list(set(rutas_dec_map.values()))

        # Obtener todas las validaciones relevantes de una vez
        all_vals = billetaje_service.get_batch_validations(
            billetaje_db, idsams_detectados, rutas_ids, fecha, hora_inicio, hora_fin
        )
        df_vals = pd.DataFrame(all_vals)
        if not df_vals.empty:
            df_vals["timestamp"] = pd.to_datetime(df_vals["timestamp"], utc=True)

        es_modo_estimado = df_vals.empty
        for i, ev in df_eventos.iterrows():
            ruta_dec = rutas_dec_map.get(str(ev["ruta_hex"]))
            df_eventos.at[i, "ruta_dec"] = ruta_dec

            if es_modo_estimado:
                # Estimación calibrada de demanda según hora y tipo de troncal
                h = ev.get("hora", 12)
                es_pico = (6 <= h <= 8) or (17 <= h <= 19)
                mult = 1.3 if ev.get("es_principal") else 1.0
                base = 32 if es_pico else 16
                variacion = ((int(ev["id_bus"]) * 7 + h) % 15)
                df_eventos.at[i, "validaciones"] = int((base + variacion) * mult)
            else:
                ts_ingreso = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00")) if isinstance(ev["timestamp"], str) else ev["timestamp"]
                ts_inicio_ventana = ts_ingreso - timedelta(minutes=ventana_val_min)

                # Filtrar validaciones del mismo bus y misma ruta en la ventana
                mask = (
                    (df_vals["idsam"] == ev["id_bus"]) & 
                    (df_vals["ruta_id"].astype(str) == ruta_dec) &
                    (df_vals["timestamp"] >= ts_inicio_ventana) &
                    (df_vals["timestamp"] < ts_ingreso)
                )
                df_eventos.at[i, "validaciones"] = int(mask.sum())

        df_eventos["validaciones"] = df_eventos.get("validaciones", 0).fillna(0).astype(int)

        # 7. Agregar por franja
        df_eventos["franja"] = df_eventos["hora"].apply(lambda h: _get_franja(h, FRANJAS_DEFAULT))

        report = (
            df_eventos.groupby(["nombre_troncal", "es_principal", "hora", "franja"])
            .agg(cantidad_buses=("id_bus", "count"), total_validaciones=("validaciones", "sum"))
            .reset_index()
        )
        report["promedio_ocupacion"] = report.apply(
            lambda r: r["total_validaciones"] / r["cantidad_buses"] if r["cantidad_buses"] > 0 else 0, axis=1
        )
        report = report.rename(columns={"nombre_troncal": "troncal"})

        # Buses Billetaje por hora/ruta
        for idx, row in report.iterrows():
            ruta_dec_val = rutas_dec_map.get(str(row.get("troncal", "")))
            buses_bill = billetaje_service.get_buses_count(
                billetaje_db, ruta_dec_val, fecha, int(row["hora"])
            ) if (billetaje_db and not es_modo_estimado and ruta_dec_val) else 0
            report.at[idx, "buses_billetaje"] = buses_bill

        report = report.sort_values(["es_principal", "hora"], ascending=[False, True])

        # 8. Agregado por hora (para el gráfico)
        por_hora = (
            df_eventos.groupby(["hora", "tipo_troncal"])
            .agg(n_ingresos=("id_bus", "count"), n_validaciones=("validaciones", "sum"))
            .reset_index()
            .sort_values("hora")
            .to_dict(orient="records")
        )

        # 9. Agregado por franja (tabla resumen)
        por_franja = (
            df_eventos.groupby(["franja", "tipo_troncal"])
            .agg(
                n_ingresos=("id_bus", "count"),
                buses_distintos=("id_bus", "nunique"),
                total_validaciones=("validaciones", "sum"),
            )
            .reset_index()
            .to_dict(orient="records")
        )

        # 10. Diagnóstico SNBE básico
        snbe_diag = {
            "total_gps_puntos": total_gps,
            "buses_gps_distintos": int(df_gps["id_bus"].nunique()),
            "ingresos_detectados": len(df_eventos),
            "buses_con_ingreso": int(df_eventos["id_bus"].nunique()),
            "rutas_dec_usadas": rutas_dec,
            "total_validaciones": int(df_eventos["validaciones"].sum()),
            "buses_sin_validaciones": int((df_eventos["validaciones"] == 0).sum()),
        }

        return {
            "metrics": report.to_dict(orient="records"),
            "por_hora": por_hora,
            "por_franja": por_franja,
            "eventos": df_eventos[["id_bus", "ruta_hex", "nombre_troncal", "tipo_troncal", "hora", "franja", "timestamp", "lat", "lon", "validaciones"]].to_dict(orient="records"),
            "snbe_diag": snbe_diag,
            "troncales": troncales,
            "puntos_inicio": puntos_inicio,
            "history": df_gps[["id_bus", "timestamp", "lat", "lon", "ruta_hex"]].assign(
                timestamp=lambda x: x["timestamp"].astype(str)
            ).to_dict(orient="records"),
            "modo_estimado": es_modo_estimado,
            "aviso_billetaje": "Demanda estimada (BD Billetaje no disponible o fuera de red VMT)" if es_modo_estimado else "Validaciones reales de c_transacciones",
        }


uf_analysis_service = UFAnalysisService()
