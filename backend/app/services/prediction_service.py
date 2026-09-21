import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PredictionService:
    """
    Servicio avanzado de predicción de atrasos y ETAs.
    Utiliza datos históricos y estado actual para proyectar la operación futura.
    """

    def __init__(self, db_session=None):
        self.db = db_session
        # Factores de congestión por franja horaria (ejemplo para demo)
        self.factores_horarios = {
            "PICO_MANANA": 1.5,   # 07:00 - 09:00
            "VALLE": 1.0,         # 10:00 - 16:00
            "PICO_TARDE": 1.8,    # 17:00 - 19:00
            "NOCHE": 0.8          # 21:00+
        }

    def _get_factor_actual(self) -> float:
        hora = datetime.now().hour
        if 7 <= hora <= 9: return self.factores_horarios["PICO_MANANA"]
        if 17 <= hora <= 19: return self.factores_horarios["PICO_TARDE"]
        if hora >= 21 or hora <= 5: return self.factores_horarios["NOCHE"]
        return self.factores_horarios["VALLE"]

    def calcular_eta_proyectado(
        self, 
        posicion_actual_m: float, 
        velocidad_actual_kmh: float,
        paraderos_restantes: List[Dict],
        v_historica_kmh: float = 22.0
    ) -> List[Dict]:
        """
        Calcula el tiempo estimado de llegada (ETA) a los paraderos restantes.
        Considera:
        1. Velocidad actual del bus.
        2. Congestión proyectada según la hora.
        3. Tiempos de parada estimados por paradero.
        """
        predicciones = []
        tiempo_acumulado_seg = 0
        factor_congestion = self._get_factor_actual()
        
        # Mezcla de velocidad actual y histórica para estabilidad
        v_proyectada = (velocidad_actual_kmh * 0.4) + (v_historica_kmh * 0.6)
        v_proyectada_ms = (v_proyectada / 3.6) / factor_congestion
        
        pos_anterior = posicion_actual_m
        
        for paradero in paraderos_restantes:
            distancia = paradero["distancia_m"] - pos_anterior
            if distancia < 0: continue # Ya pasó el paradero
            
            # Tiempo de viaje entre puntos
            tiempo_viaje = distancia / max(v_proyectada_ms, 1.0)
            
            # Tiempo de parada estimado (basado en 'importancia' del paradero)
            t_parada = 30 # segundos base
            if paradero.get("tipo") == "TERMINAL": t_parada = 0
            
            tiempo_acumulado_seg += tiempo_viaje + t_parada
            pos_anterior = paradero["distancia_m"]
            
            eta_timestamp = datetime.now() + timedelta(seconds=tiempo_acumulado_seg)
            
            predicciones.append({
                "id_paradero": paradero["id_paradero"],
                "nombre": paradero["nombre"],
                "distancia_restante_m": round(distancia, 0),
                "eta_segundos": round(tiempo_acumulado_seg, 0),
                "eta_minutos": round(tiempo_acumulado_seg / 60, 1),
                "hora_estimada": eta_timestamp.isoformat(),
                "atraso_proyectado_min": round((tiempo_acumulado_seg / 60) * 0.15, 1) # Heurística de atraso
            })
            
        return predicciones

    def optimizar_frecuencia(
        self, 
        demanda_pax_hora: float, 
        capacidad_bus: int, 
        tiempo_ciclo_min: float
    ) -> Dict:
        """
        Sugiere el intervalo (headway) óptimo para minimizar el tiempo de espera
        sin saturar la flota.
        """
        # Regla de oro: El intervalo debe ser suficiente para evacuar la demanda
        # buses_necesarios = demanda / (capacidad * factor_carga)
        factor_carga_deseado = 0.8
        buses_necesarios = (demanda_pax_hora * (tiempo_ciclo_min/60)) / (capacidad_bus * factor_carga_deseado)
        buses_necesarios = max(2, int(np.ceil(buses_necesarios)))
        
        headway_optimo = tiempo_ciclo_min / buses_necesarios
        
        return {
            "headway_sugerido_min": round(headway_optimo, 1),
            "buses_necesarios": buses_necesarios,
            "capacidad_total_hora": int(buses_necesarios * capacidad_bus * (60 / headway_optimo)),
            "nivel_servicio_estimado": "A" if headway_optimo <= 5 else "B" if headway_optimo <= 10 else "C"
        }

prediction_service = PredictionService()
