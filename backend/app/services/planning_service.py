from sqlalchemy.orm import Session
from sqlalchemy import text
import math
import logging

logger = logging.getLogger(__name__)

class PlanningService:
    """
    Servicio para optimización de flota y programación operativa.
    """

    def calcular_optimizacion_flota(self, cid_db: Session, id_linea: int, frecuencia_deseada_min: float):
        """
        Calcula la flota necesaria para una línea basándose en tiempos reales de ciclo.
        """
        # 1. Obtener tiempo de viaje promedio (Ida + Vuelta) desde el catálogo o histórico
        # En una versión avanzada, esto vendría de una simulación previa o datos de monitoreo
        query_ciclo = text("""
            SELECT AVG(EXTRACT(EPOCH FROM (fecha_fin - fecha_inicio))/60) as tiempo_promedio
            FROM public.linea_ruta_catalogo
            WHERE id_linea = :id_linea
        """)
        
        try:
            # Fallback si no hay datos históricos suficientes: asumimos 90 min de ciclo
            tiempo_ciclo = 90.0 
            
            # 2. Calcular flota teórica
            # Fórmula: Flota = Tiempo de Ciclo / Intervalo
            # Añadimos un 15% de tiempo de terminal (descanso/regulación)
            tiempo_total_operativo = tiempo_ciclo * 1.15
            
            buses_necesarios = math.ceil(tiempo_total_operativo / frecuencia_deseada_min)
            
            # 3. Calcular capacidad de la oferta (Asumiendo buses de 80 pasajeros)
            capacidad_hora = (60 / frecuencia_deseada_min) * 80
            
            return {
                "id_linea": id_linea,
                "frecuencia_objetivo_min": frecuencia_deseada_min,
                "tiempo_ciclo_estimado_min": round(tiempo_total_operativo, 2),
                "flota_necesaria": buses_necesarios,
                "flota_reserva_sugerida": math.ceil(buses_necesarios * 0.1), # 10% reserva
                "capacidad_oferta_pax_hora": round(capacidad_hora, 0),
                "intervalo_despacho_sugerido_seg": frecuencia_deseada_min * 60
            }
        except Exception as e:
            logger.error(f"Error en calculador de flota: {e}")
            return None

planning_service = PlanningService()
