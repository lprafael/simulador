from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CidService:
    """
    Servicio para interactuar directamente con la infraestructura real de SisCID.
    """
    
    def get_lineas_reales(self, cid_db: Session) -> List[Dict[str, Any]]:
        """Consulta la tabla maestra de líneas (public.lineas)."""
        query = text("""
            SELECT id_linea, numero_linea, nombre_comercial, identificador_troncal, estado, color_hex
            FROM public.lineas
            WHERE estado = TRUE
            ORDER BY numero_linea
        """)
        try:
            result = cid_db.execute(query)
            rows = [dict(row._asdict()) for row in result]
            logger.info(f"📡 CID DB Query Exitosa. Filas obtenidas: {len(rows)}")
            return rows
        except Exception as e:
            logger.error(f"❌ Error consultando líneas maestras en CID: {e}")
            return []

    def get_lineas_por_uf(self, cid_db: Session, id_uf: int) -> List[Dict[str, Any]]:
        """Obtiene las líneas vinculadas a una UF a través de la tabla de composición."""
        # En SisCID composicion_uf está en el esquema gestion_uf
        query = text("""
            SELECT DISTINCT l.id_linea, l.numero_linea, l.nombre_comercial, l.color_hex
            FROM public.lineas l
            JOIN public.linea_ruta_catalogo lrc ON l.id_linea = lrc.id_linea
            JOIN gestion_uf.composicion_uf c ON lrc.ruta_hex = c.ruta_hex
            WHERE c.id_uf = :id_uf
              AND (c.fecha_fin IS NULL OR c.fecha_fin >= CURRENT_DATE)
            ORDER BY l.numero_linea
        """)
        try:
            result = cid_db.execute(query, {"id_uf": id_uf})
            return [dict(row._asdict()) for row in result]
        except Exception as e:
            logger.error(f"Error consultando líneas de la UF {id_uf}: {e}")
            cid_db.rollback()
            return []

    def get_rutas_por_linea(self, cid_db: Session, id_linea: int) -> List[Dict[str, Any]]:
        """Obtiene las rutas técnicas vinculadas a una línea."""
        query = text("""
            SELECT r.ruta_hex, r.sentido
            FROM public.catalogo_rutas r
            JOIN public.linea_ruta_catalogo lrc ON r.ruta_hex = lrc.ruta_hex
            WHERE lrc.id_linea = :id_linea
              AND (lrc.fecha_fin IS NULL OR lrc.fecha_fin >= CURRENT_DATE)
        """)
        try:
            result = cid_db.execute(query, {"id_linea": id_linea})
            return [dict(row._asdict()) for row in result]
        except Exception as e:
            logger.error(f"Error consultando rutas de la línea {id_linea}: {e}")
            # Importante: No dejar la transacción abortada
            cid_db.rollback()
            return []

    def get_paraderos_por_ruta(self, cid_db: Session, ruta_hex: str) -> List[Dict[str, Any]]:
        """Obtiene los paraderos oficiales para una ruta específica."""
        query = text("""
            SELECT id_paradero, nombre, orden_ruta, latitud, longitud, distancia_m
            FROM public.paraderos
            WHERE ruta_hex = :ruta_hex
              AND estado = TRUE
            ORDER BY orden_ruta ASC
        """)
        try:
            result = cid_db.execute(query, {"ruta_hex": ruta_hex})
            return [dict(row._asdict()) for row in result]
        except Exception as e:
            logger.debug(f"Nota: No se encontraron paraderos en public.paraderos para ruta {ruta_hex}: {e}")
            cid_db.rollback()
            return []

    def get_geometria_ruta(self, cid_db: Session, ruta_hex: str) -> Dict[str, Any]:
        """Obtiene el LineString (GeoJSON) del itinerario actual de una ruta."""
        query = text("""
            SELECT ST_AsGeoJSON(geom) as geojson
            FROM geometria.historico_itinerario
            WHERE ruta_hex = :ruta_hex
            ORDER BY fecha_inicio_vigencia DESC
            LIMIT 1
        """)
        try:
            result = cid_db.execute(query, {"ruta_hex": ruta_hex}).first()
            return dict(result._asdict()) if result else None
        except Exception as e:
            logger.error(f"Error consultando geometría de ruta {ruta_hex}: {e}")
            return None

    def get_estructura_uf(self, cid_db: Session, id_uf: int = None) -> List[Dict[str, Any]]:
        """
        Consulta la relación entre UFs, Consorcios y EOTs.
        Ajustado para manejar diferencias de esquema entre local y SisCID.
        """
        # Intentamos la query adaptada a la realidad del SisCID detectada (public.consorcios)
        query = text("""
            SELECT 
                uf.id_uf,
                uf.nombre_uf as uf_nombre,
                c.nombre as consorcio_nombre,
                e.eot_nombre as empresa_nombre,
                e.id_eot_vmt_hex as codigo_eot
            FROM gestion_uf.unidades_funcionales uf
            LEFT JOIN gestion_uf.contratos ct ON uf.id_uf = ct.id_uf
            LEFT JOIN gestion_uf.composicion_consorcio cc ON ct.id_eot = cc.id_eot
            LEFT JOIN public.consorcios c ON cc.id_consorcio = c.id_consorcio
            LEFT JOIN public.eots e ON cc.id_eot = e.eot_id
            WHERE (:id_uf IS NULL OR uf.id_uf = :id_uf)
        """)
        
        # Si la query anterior falla por columnas faltantes (ej: en local es distinto), 
        # usamos un fallback más simple.
        query_fallback = text("""
            SELECT 
                uf.id_uf,
                uf.nombre_uf as uf_nombre,
                NULL as consorcio_nombre,
                NULL as empresa_nombre,
                NULL as codigo_eot
            FROM gestion_uf.unidades_funcionales uf
            WHERE (:id_uf IS NULL OR uf.id_uf = :id_uf)
        """)

        try:
            result = cid_db.execute(query, {"id_uf": id_uf})
            rows = [dict(row._asdict()) for row in result]
            return rows
        except Exception as e:
            cid_db.rollback()
            logger.warning(f"⚠️ Error en query UF compleja: {e}. Intentando fallback simple...")
            try:
                result = cid_db.execute(query_fallback, {"id_uf": id_uf})
                return [dict(row._asdict()) for row in result]
            except Exception as e2:
                cid_db.rollback()
                logger.error(f"❌ Error crítico consultando UFs en CID: {e2}")
                return []

    def get_historico_gps_uf(self, cid_db: Session, monitoreo_db: Session, id_uf: int, fecha: str) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de posiciones para todas las rutas de una UF en una fecha dada.
        Usa CID_DB para catálogos y MONITOREO_DB para posiciones GPS reales.
        """
        # 1. Obtener agencias (id_eot_vmt_hex) y rutas (ruta_hex) asociadas a la UF
        query_catalog = text("""
            SELECT DISTINCT e.id_eot_vmt_hex as agency_id, r.ruta_hex
            FROM gestion_uf.composicion_uf c
            JOIN public.catalogo_rutas r ON c.ruta_hex = r.ruta_hex
            JOIN public.eots e ON r.id_eot_catalogo = e.cod_catalogo
            WHERE c.id_uf = :id_uf
              AND (c.fecha_fin IS NULL OR c.fecha_fin >= CAST(:fecha AS DATE))
              AND c.fecha_inicio <= CAST(:fecha AS DATE)
        """)
        
        try:
            res_catalog = cid_db.execute(query_catalog, {"id_uf": id_uf, "fecha": fecha}).fetchall()
            if not res_catalog:
                return []
            
            agency_ids = list(set([r.agency_id for r in res_catalog if r.agency_id]))
            route_ids = list(set([r.ruta_hex for r in res_catalog if r.ruta_hex]))
            
            logger.info(f"🔎 UF {id_uf} en {fecha}: Agencias={agency_ids}, Rutas={route_ids}")

            if not agency_ids or not route_ids:
                logger.warning(f"⚠️ No se encontraron agencias o rutas para la UF {id_uf}")
                return []

            # 2. Consultar GPS en la DB de Monitoreo
            query_gps = text("""
                SELECT 
                    latitude as lat, 
                    longitude as lon, 
                    fecha_hora as timestamp, 
                    route_id as ruta_hex,
                    identidad as id_bus,
                    velocidad,
                    rumbo
                FROM public.app_monitoreo_mensajeoperativo
                WHERE agency_id IN :agencies
                  AND route_id IN :routes
                  AND fecha_hora::date = CAST(:fecha AS DATE)
                ORDER BY fecha_hora ASC
                LIMIT 5000
            """)
            
            result = monitoreo_db.execute(query_gps, {
                "agencies": tuple(agency_ids),
                "routes": tuple(route_ids),
                "fecha": fecha
            })
            
            rows = [dict(row._asdict()) for row in result]
            logger.info(f"✅ Se obtuvieron {len(rows)} posiciones GPS para UF {id_uf}")
            return rows
            
        except Exception as e:
            logger.error(f"Error consultando histórico GPS para UF {id_uf} en {fecha}: {e}")
            if cid_db: cid_db.rollback()
            if monitoreo_db: monitoreo_db.rollback()
            return []

    def get_uf_troncales(self, cid_db: Session, id_uf: int) -> List[Dict[str, Any]]:
        """Obtiene las troncales (principales y secundarias) de una UF con su geometría."""
        query = text("""
            SELECT 
                id_troncal, 
                nombre, 
                es_principal, 
                color_hex,
                ST_AsGeoJSON(geom) as geojson
            FROM gestion_uf.uf_troncales
            WHERE id_uf = :id_uf AND activo = TRUE
        """)
        try:
            result = cid_db.execute(query, {"id_uf": id_uf})
            return [dict(row._asdict()) for row in result]
        except Exception as e:
            logger.error(f"Error consultando troncales de UF {id_uf}: {e}")
            cid_db.rollback()
            return []

    def get_puntos_inicio_uf(self, cid_db: Session, id_uf: int) -> List[Dict[str, Any]]:
        """Obtiene el punto inicial de cada ruta que compone la UF."""
        query = text("""
            SELECT DISTINCT
                c.ruta_hex,
                ST_AsGeoJSON(ST_StartPoint(h.geom)) as geojson
            FROM gestion_uf.composicion_uf c
            JOIN geometria.historico_itinerario h ON c.ruta_hex = h.ruta_hex
            WHERE c.id_uf = :id_uf
              AND (c.fecha_fin IS NULL OR c.fecha_fin >= CURRENT_DATE)
              AND h.fecha_fin_vigencia IS NULL
        """)
        try:
            result = cid_db.execute(query, {"id_uf": id_uf})
            return [dict(row._asdict()) for row in result]
        except Exception as e:
            logger.error(f"Error consultando puntos de inicio de UF {id_uf}: {e}")
            cid_db.rollback()
            return []

    def get_geocercas_uf(self, cid_db: Session, id_uf: int) -> List[Dict[str, Any]]:
        """
        Obtiene las geocercas relacionadas con la UF:
        - Tipo 1: Geocercas de inicio de itinerarios.
        - Tipo 7: Geocercas de troncales (buffer 50m).
        """
        query = text("""
            -- Geocercas de Inicio (Tipo 1)
            SELECT 
                g.id_geocerca,
                g.id_tipo,
                tg.descripcion as tipo_nombre,
                ST_AsGeoJSON(g.geom) as geojson,
                h.ruta_hex,
                False as es_principal
            FROM geometria.geocercas g
            JOIN geometria.tipos_geocerca tg ON g.id_tipo = tg.id_tipo
            JOIN geometria.historico_itinerario h ON g.id_itinerario = h.id_itinerario
            JOIN gestion_uf.composicion_uf c ON h.ruta_hex = c.ruta_hex
            WHERE c.id_uf = :id_uf
              AND g.id_tipo IN (1, 3)
              AND c.fecha_inicio <= CURRENT_DATE
              AND (c.fecha_fin IS NULL OR c.fecha_fin >= CURRENT_DATE)
              AND h.fecha_fin_vigencia IS NULL

            UNION ALL

            -- Geocercas de Troncales (Tipo 7)
            SELECT 
                g.id_geocerca,
                g.id_tipo,
                tg.descripcion as tipo_nombre,
                ST_AsGeoJSON(g.geom) as geojson,
                t.nombre as ruta_hex, -- Usamos el campo para el nombre de la troncal
                t.es_principal
            FROM geometria.geocercas g
            JOIN geometria.tipos_geocerca tg ON g.id_tipo = tg.id_tipo
            JOIN gestion_uf.uf_troncales t ON g.id_troncal_uf = t.id_troncal
            WHERE t.id_uf = :id_uf
              AND g.id_tipo = 7
              AND t.activo = TRUE
        """)
        try:
            result = cid_db.execute(query, {"id_uf": id_uf})
            return [dict(row._asdict()) for row in result]
        except Exception as e:
            logger.error(f"Error consultando geocercas de UF {id_uf}: {e}")
            cid_db.rollback()
            return []

cid_service = CidService()
