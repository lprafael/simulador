import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)

class BilletajeService:
    """
    Servicio para manejar la demanda de pasajeros. 
    Actualmente en modo Simulado hasta configurar conexión real.
    """

    def generar_matriz_od_avanzada(
        self, 
        billetaje_db: Session, 
        fecha: date,
        umbral_transbordo_min: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Genera la Matriz Origen-Destino real utilizando algoritmos de Trip Chaining 
        sobre la tabla c_transacciones.
        """
        if not billetaje_db:
            return self._generar_simulado()

        logger.info(f"📊 Generando Matriz OD real para fecha {fecha} desde c_transacciones...")
        
        try:
            # Query base para obtener transacciones ordenadas por tarjeta y tiempo
            # NOTA: Ajustar nombres de columnas según esquema real de c_transacciones
            query = text("""
                WITH transacciones_dia AS (
                    SELECT 
                        serialmediopago as id_tarjeta, 
                        fechahoraevento as fecha_hora, 
                        idubicacion as id_paradero,
                        idrutaestacion as id_linea,
                        LAG(idubicacion) OVER (PARTITION BY serialmediopago ORDER BY fechahoraevento) as origen_previo,
                        LEAD(idubicacion) OVER (PARTITION BY serialmediopago ORDER BY fechahoraevento) as destino_inferido
                    FROM c_transacciones
                    WHERE fechahoraevento::date = :fecha
                )
                SELECT 
                    id_paradero as origen_id, 
                    destino_inferido as destino_estimado_id, 
                    COUNT(*) as cantidad_viajes
                FROM transacciones_dia
                WHERE destino_inferido IS NOT NULL
                GROUP BY id_paradero, destino_inferido
                HAVING COUNT(*) > 2
                ORDER BY cantidad_viajes DESC
                LIMIT 100;
            """)
            
            result = billetaje_db.execute(query, {"fecha": fecha})
            filas = result.fetchall()
            
            if not filas:
                logger.warning("⚠️ No se encontraron datos en c_transacciones para la fecha seleccionada.")
                return self._generar_simulado()
                
            return [dict(f._asdict()) for f in filas]
            
        except Exception as e:
            logger.error(f"❌ Error consultando billetaje (c_transacciones): {e}")
            return self._generar_simulado()

    def get_demanda_historica(
        self, 
        billetaje_db: Session, 
        id_linea: int, 
        inicio: datetime, 
        fin: datetime
    ) -> List[Dict[str, Any]]:
        """Obtiene el histórico de ascensos por paradero para alimentar el motor de simulación."""
        if not billetaje_db:
            return []
            
        try:
            query = text("""
                SELECT 
                    idubicacion as id_paradero, 
                    COUNT(*) as ascensos,
                    EXTRACT(MINUTE FROM fechahoraevento) as minuto_sim
                FROM c_transacciones
                WHERE idrutaestacion = :id_linea 
                  AND fechahoraevento BETWEEN :inicio AND :fin
                GROUP BY idubicacion, EXTRACT(MINUTE FROM fechahoraevento)
                ORDER BY minuto_sim;
            """)
            result = billetaje_db.execute(query, {"id_linea": id_linea, "inicio": inicio, "fin": fin})
            return [dict(f._asdict()) for f in result.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error en get_demanda_historica: {e}")
            return []

    def get_perfil_demanda_diaria(self, billetaje_db: Session, id_linea: int) -> List[Dict[str, Any]]:
        """Obtiene el perfil de carga horaria de una línea."""
        if not billetaje_db:
            return []
            
        try:
            query = text("""
                SELECT 
                    EXTRACT(HOUR FROM fechahoraevento) as hora, 
                    COUNT(*) as total_pasajeros
                FROM c_transacciones
                WHERE idrutaestacion = :id_linea
                GROUP BY EXTRACT(HOUR FROM fechahoraevento)
                ORDER BY hora;
            """)
            result = billetaje_db.execute(query, {"id_linea": id_linea})
            return [dict(f._asdict()) for f in result.fetchall()]
        except Exception as e:
            logger.error(f"❌ Error en get_perfil_demanda_diaria: {e}")
            return []

    def _generar_simulado(self) -> List[Dict[str, Any]]:
        """Fallback con datos de prueba si falla la conexión real."""
        return [
            {"origen_id": 1, "destino_estimado_id": 10, "cantidad_viajes": 550},
            {"origen_id": 5, "destino_estimado_id": 12, "cantidad_viajes": 320},
            {"origen_id": 8, "destino_estimado_id": 2, "cantidad_viajes": 180},
            {"origen_id": 15, "destino_estimado_id": 20, "cantidad_viajes": 410},
            {"origen_id": 3, "destino_estimado_id": 30, "cantidad_viajes": 290}
        ]

    def get_validations_count(
        self, 
        billetaje_db: Session, 
        id_bus: str, 
        ruta_id: int, 
        timestamp_limit: datetime,
        ventana_min: int = 60
    ) -> int:
        # Mantenemos este método para compatibilidad, pero uf_analysis_service usará el batch
        res = self.get_batch_validations(
            billetaje_db, [id_bus], [str(ruta_id)], timestamp_limit.date(), 
            timestamp_limit.hour, timestamp_limit.hour + 1
        )
        return len(res)

    def get_batch_validations(
        self,
        billetaje_db: Session,
        idsams: List[str],
        rutas_ids: List[str],
        fecha: date,
        hora_inicio: int,
        hora_fin: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las validaciones para un conjunto de buses y rutas en una ventana horaria.
        Eficaz para evitar N queries al simular carga de UF.
        """
        if not billetaje_db or not idsams or not rutas_ids:
            return []

        query = text("""
            SELECT 
                idsam, 
                idrutaestacion as ruta_id, 
                fechahoraevento as timestamp
            FROM c_transacciones
            WHERE idsam IN :idsams
              AND idrutaestacion IN :rutas_ids
              AND fechahoraevento >= :start_ts
              AND fechahoraevento < :end_ts
        """)
        
        start_ts = datetime.combine(fecha, datetime.min.time()).replace(hour=max(0, hora_inicio - 1))
        end_ts = datetime.combine(fecha, datetime.min.time()).replace(hour=min(23, hora_fin + 1), minute=59)
        
        try:
            result = billetaje_db.execute(query, {
                "idsams": tuple(idsams),
                "rutas_ids": tuple(rutas_ids),
                "start_ts": start_ts,
                "end_ts": end_ts
            }).fetchall()
            return [dict(r._asdict()) for r in result]
        except Exception as e:
            logger.warning(f"Error en get_batch_validations (fallback activo): {e}")
            try:
                billetaje_db.rollback()
            except Exception:
                pass
            return []

    def get_buses_count(self, billetaje_db: Session, ruta_id: int, fecha: datetime.date, hora: int) -> int:
        """
        Retorna la cantidad de buses distintos (idsam) que tuvieron validaciones 
        en una ruta y hora específica.
        """
        if not billetaje_db:
            return 0
            
        query = text("""
            SELECT COUNT(DISTINCT idsam)
            FROM c_transacciones
            WHERE idrutaestacion = :ruta_id
              AND fechahoraevento >= :start_hour
              AND fechahoraevento < :end_hour
        """)
        
        start_hour = datetime.combine(fecha, datetime.min.time()).replace(hour=hora)
        end_hour = start_hour + timedelta(hours=1)
        
        try:
            result = billetaje_db.execute(query, {
                "ruta_id": ruta_id,
                "start_hour": start_hour,
                "end_hour": end_hour
            }).fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.warning(f"Error consultando buses en billetaje para ruta {ruta_id}: {e}")
            try:
                billetaje_db.rollback()
            except Exception:
                pass
            return 0

billetaje_service = BilletajeService()
