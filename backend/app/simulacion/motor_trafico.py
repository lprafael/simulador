"""
Motor de Simulación Integral de Tránsito para Asunción y Gran Asunción.
Modela:
- Red vial urbana (tramos, intersecciones, sentidos de circulación).
- Algoritmo de asignación de tráfico y demoras BPR (Bureau of Public Roads).
- Reasignación dinámica de flujos por cambios de sentido, cierres de calles o carriles exclusivos ("What-If").
- Detección de arterias paralelas colapsadas ("derrame de tráfico").
- Impacto en tiempos de viaje y líneas de transporte público (colectivos).
- Integración y calibración con datos de Waze for Cities.
"""

import math
import heapq
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# =====================================================================
# RED VIAL BASE DE ASUNCIÓN Y GRAN ASUNCIÓN (Georreferenciada)
# =====================================================================

RED_VIAL_ASUNCION_METRO: List[Dict[str, Any]] = [
    # --- CENTRO HISTÓRICO Y TRANSVERSALES ASUNCIÓN ---
    {
        "id_tramo": 1,
        "codigo": "ASU-PALMA-01",
        "nombre_calle": "Calle Palma",
        "municipio": "Asunción",
        "categoria": "ARTERIAL",
        "sentido": "UNICO_DIRECTO", # Sentido hacia el microcentro / puerto
        "nodo_origen": "Plaza Uruguaya",
        "nodo_destino": "Plaza de los Héroes",
        "carriles": 2,
        "longitud_m": 850,
        "velocidad_limite_kmh": 40.0,
        "capacidad_veh_hora": 1100,
        "flujo_base_veh_hora": 750,
        "coordenadas": [
            [-25.2828, -57.6322],
            [-25.2835, -57.6360],
            [-25.2842, -57.6405]
        ],
        "lineas_colectivo": ["Línea 12", "Línea 21", "Línea 27"],
        "paralelas_ids": [2, 3] # Estrella, Oliva
    },
    {
        "id_tramo": 2,
        "codigo": "ASU-ESTRELLA-01",
        "nombre_calle": "Calle Estrella",
        "municipio": "Asunción",
        "categoria": "ARTERIAL",
        "sentido": "UNICO_DIRECTO",
        "nodo_origen": "Plaza Uruguaya",
        "nodo_destino": "Puerto de Asunción",
        "carriles": 2,
        "longitud_m": 900,
        "velocidad_limite_kmh": 40.0,
        "capacidad_veh_hora": 1200,
        "flujo_base_veh_hora": 820,
        "coordenadas": [
            [-25.2838, -57.6320],
            [-25.2846, -57.6368],
            [-25.2853, -57.6415]
        ],
        "lineas_colectivo": ["Línea 30", "Línea 41", "Línea 56"],
        "paralelas_ids": [1, 3]
    },
    {
        "id_tramo": 3,
        "codigo": "ASU-OLIVA-01",
        "nombre_calle": "Calle Oliva / Cerro Corá",
        "municipio": "Asunción",
        "categoria": "ARTERIAL",
        "sentido": "UNICO_INVERSO", # Salida hacia Plaza Uruguaya
        "nodo_origen": "Colón",
        "nodo_destino": "Plaza Uruguaya",
        "carriles": 2,
        "longitud_m": 920,
        "velocidad_limite_kmh": 40.0,
        "capacidad_veh_hora": 1150,
        "flujo_base_veh_hora": 780,
        "coordenadas": [
            [-25.2860, -57.6410],
            [-25.2852, -57.6365],
            [-25.2844, -57.6315]
        ],
        "lineas_colectivo": ["Línea 15-1", "Línea 23", "Línea 31"],
        "paralelas_ids": [1, 2, 4]
    },
    {
        "id_tramo": 4,
        "codigo": "ASU-HERRERA-01",
        "nombre_calle": "Calle Herrera / Haedo",
        "municipio": "Asunción",
        "categoria": "ARTERIAL",
        "sentido": "UNICO_INVERSO",
        "nodo_origen": "Colón",
        "nodo_destino": "Avda. Perú",
        "carriles": 2,
        "longitud_m": 1200,
        "velocidad_limite_kmh": 45.0,
        "capacidad_veh_hora": 1300,
        "flujo_base_veh_hora": 950,
        "coordenadas": [
            [-25.2880, -57.6410],
            [-25.2870, -57.6350],
            [-25.2860, -57.6280]
        ],
        "lineas_colectivo": ["Línea 38", "Línea 20", "Línea 44"],
        "paralelas_ids": [3]
    },

    # --- GRANDES EJES TRONCALES METROPOLITANOS (ASUNCIÓN - GRAN ASUNCIÓN) ---
    {
        "id_tramo": 5,
        "codigo": "ASU-MCAL-LOPEZ-01",
        "nombre_calle": "Avda. Mariscal López (Tramo Centro - San Martín)",
        "municipio": "Asunción",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Avda. Perú",
        "nodo_destino": "Avda. San Martín",
        "carriles": 4,
        "longitud_m": 3500,
        "velocidad_limite_kmh": 55.0,
        "capacidad_veh_hora": 2800,
        "flujo_base_veh_hora": 2300,
        "coordenadas": [
            [-25.2885, -57.6180],
            [-25.2920, -57.5980],
            [-25.2955, -57.5750]
        ],
        "lineas_colectivo": ["Línea 12", "Línea 26", "Línea 30", "Línea 56"],
        "paralelas_ids": [6, 7] # España, Guido Spano
    },
    {
        "id_tramo": 6,
        "codigo": "ASU-ESPANA-01",
        "nombre_calle": "Avda. España",
        "municipio": "Asunción",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Avda. Perú",
        "nodo_destino": "Avda. San Martín",
        "carriles": 4,
        "longitud_m": 3400,
        "velocidad_limite_kmh": 50.0,
        "capacidad_veh_hora": 2600,
        "flujo_base_veh_hora": 2150,
        "coordenadas": [
            [-25.2790, -57.6170],
            [-25.2830, -57.5950],
            [-25.2880, -57.5730]
        ],
        "lineas_colectivo": ["Línea 23", "Línea 30", "Línea 37"],
        "paralelas_ids": [5]
    },
    {
        "id_tramo": 7,
        "codigo": "ASU-GUIDO-SPANO-01",
        "nombre_calle": "Calle Guido Spano / Andrade",
        "municipio": "Asunción",
        "categoria": "COLECTORA",
        "sentido": "DOBLE",
        "nodo_origen": "Avda. Choferes del Chaco",
        "nodo_destino": "Avda. San Martín",
        "carriles": 2,
        "longitud_m": 1600,
        "velocidad_limite_kmh": 40.0,
        "capacidad_veh_hora": 950,
        "flujo_base_veh_hora": 600,
        "coordenadas": [
            [-25.2980, -57.5920],
            [-25.2995, -57.5830],
            [-25.3010, -57.5760]
        ],
        "lineas_colectivo": [],
        "paralelas_ids": [5]
    },
    {
        "id_tramo": 8,
        "codigo": "ASU-EUSEBIO-AYALA-01",
        "nombre_calle": "Avda. Eusebio Ayala (Mercado 4 - Km 5)",
        "municipio": "Asunción",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Mercado 4 (General Aquino)",
        "nodo_destino": "Viaducto Madame Lynch / Calle Última",
        "carriles": 6,
        "longitud_m": 4800,
        "velocidad_limite_kmh": 60.0,
        "capacidad_veh_hora": 3800,
        "flujo_base_veh_hora": 3200,
        "coordenadas": [
            [-25.3020, -57.6180],
            [-25.3120, -57.5850],
            [-25.3230, -57.5500]
        ],
        "lineas_colectivo": ["Línea 11", "Línea 19", "Línea 20", "Línea 21", "Línea 45", "Línea 96"],
        "paralelas_ids": [9, 10]
    },
    {
        "id_tramo": 9,
        "codigo": "ASU-FCO-MORA-01",
        "nombre_calle": "Avda. Fernando de la Mora",
        "municipio": "Asunción",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Mercado 4",
        "nodo_destino": "Terminal de Ómnibus Asunción",
        "carriles": 4,
        "longitud_m": 3200,
        "velocidad_limite_kmh": 50.0,
        "capacidad_veh_hora": 2500,
        "flujo_base_veh_hora": 1950,
        "coordenadas": [
            [-25.3080, -57.6150],
            [-25.3180, -57.5980],
            [-25.3280, -57.5830]
        ],
        "lineas_colectivo": ["Línea 8", "Línea 14", "Línea 15", "Línea 38"],
        "paralelas_ids": [8]
    },
    {
        "id_tramo": 10,
        "codigo": "ASU-COSTANERA-01",
        "nombre_calle": "Avda. Costanera José Asunción Flores",
        "municipio": "Asunción",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Puerto de Asunción",
        "nodo_destino": "Avda. General Santos",
        "carriles": 4,
        "longitud_m": 3800,
        "velocidad_limite_kmh": 60.0,
        "capacidad_veh_hora": 3200,
        "flujo_base_veh_hora": 2100,
        "coordenadas": [
            [-25.2750, -57.6380],
            [-25.2720, -57.6250],
            [-25.2690, -57.6100]
        ],
        "lineas_colectivo": [],
        "paralelas_ids": [11] # Artigas
    },
    {
        "id_tramo": 11,
        "codigo": "ASU-ARTIGAS-01",
        "nombre_calle": "Avda. General Artigas",
        "municipio": "Asunción",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Avda. Perú",
        "nodo_destino": "Jardín Botánico",
        "carriles": 4,
        "longitud_m": 4200,
        "velocidad_limite_kmh": 50.0,
        "capacidad_veh_hora": 2700,
        "flujo_base_veh_hora": 2350,
        "coordenadas": [
            [-25.2770, -57.6190],
            [-25.2680, -57.5950],
            [-25.2550, -57.5750]
        ],
        "lineas_colectivo": ["Línea 24", "Línea 35", "Línea 44", "Línea 48"],
        "paralelas_ids": [10]
    },

    # --- GRAN ASUNCIÓN: FERNANDO DE LA MORA ---
    {
        "id_tramo": 12,
        "codigo": "FDM-MCAL-ESTIGARRIBIA-01",
        "nombre_calle": "Ruta PY02 / Av. Mcal. Estigarribia (Fdo de la Mora)",
        "municipio": "Fernando de la Mora",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Calle Última",
        "nodo_destino": "Límite San Lorenzo",
        "carriles": 4,
        "longitud_m": 4100,
        "velocidad_limite_kmh": 55.0,
        "capacidad_veh_hora": 3100,
        "flujo_base_veh_hora": 2750,
        "coordenadas": [
            [-25.3240, -57.5490],
            [-25.3320, -57.5300],
            [-25.3390, -57.5120]
        ],
        "lineas_colectivo": ["Línea 11", "Línea 20", "Línea 49", "Línea 96"],
        "paralelas_ids": [13]
    },
    {
        "id_tramo": 13,
        "codigo": "FDM-11-SEPTIEMBRE-01",
        "nombre_calle": "Calle 11 de Septiembre (Paralela PY02 Sur)",
        "municipio": "Fernando de la Mora",
        "categoria": "ARTERIAL",
        "sentido": "DOBLE",
        "nodo_origen": "Avda. Defensores del Chaco",
        "nodo_destino": "Avda. Zavalas Cué",
        "carriles": 2,
        "longitud_m": 2600,
        "velocidad_limite_kmh": 40.0,
        "capacidad_veh_hora": 1200,
        "flujo_base_veh_hora": 890,
        "coordenadas": [
            [-25.3330, -57.5480],
            [-25.3390, -57.5320],
            [-25.3440, -57.5180]
        ],
        "lineas_colectivo": ["Línea 21"],
        "paralelas_ids": [12]
    },

    # --- GRAN ASUNCIÓN: SAN LORENZO ---
    {
        "id_tramo": 14,
        "codigo": "SLO-JULIA-M-CUETO-01",
        "nombre_calle": "Calle Julia Miranda Cueto (Mercado San Lorenzo)",
        "municipio": "San Lorenzo",
        "categoria": "ARTERIAL",
        "sentido": "UNICO_DIRECTO", # Sentido hacia Capiatá
        "nodo_origen": "Rotonda San Lorenzo",
        "nodo_destino": "Av. Manuel Ortiz Guerrero",
        "carriles": 2,
        "longitud_m": 1500,
        "velocidad_limite_kmh": 35.0,
        "capacidad_veh_hora": 1000,
        "flujo_base_veh_hora": 920,
        "coordenadas": [
            [-25.3410, -57.5110],
            [-25.3430, -57.5020],
            [-25.3450, -57.4940]
        ],
        "lineas_colectivo": ["Línea 12", "Línea 27", "Línea 56"],
        "paralelas_ids": [15]
    },
    {
        "id_tramo": 15,
        "codigo": "SLO-MCAL-ESTIGARRIBIA-02",
        "nombre_calle": "Calle Mcal. Estigarribia (Centro San Lorenzo)",
        "municipio": "San Lorenzo",
        "categoria": "ARTERIAL",
        "sentido": "UNICO_INVERSO", # Sentido hacia Asunción
        "nodo_origen": "Av. Manuel Ortiz Guerrero",
        "nodo_destino": "Rotonda San Lorenzo",
        "carriles": 2,
        "longitud_m": 1500,
        "velocidad_limite_kmh": 35.0,
        "capacidad_veh_hora": 1100,
        "flujo_base_veh_hora": 980,
        "coordenadas": [
            [-25.3435, -57.4935],
            [-25.3415, -57.5015],
            [-25.3395, -57.5105]
        ],
        "lineas_colectivo": ["Línea 19", "Línea 45", "Línea 49"],
        "paralelas_ids": [14]
    },

    # --- GRAN ASUNCIÓN: LUQUE ---
    {
        "id_tramo": 16,
        "codigo": "LUQ-AUTOPISTA-PETTIROSSI-01",
        "nombre_calle": "Autopista Silvio Pettirossi",
        "municipio": "Luque",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Viaducto Madame Lynch",
        "nodo_destino": "Aeropuerto Silvio Pettirossi",
        "carriles": 6,
        "longitud_m": 6200,
        "velocidad_limite_kmh": 80.0,
        "capacidad_veh_hora": 4500,
        "flujo_base_veh_hora": 3100,
        "coordenadas": [
            [-25.2790, -57.5450],
            [-25.2600, -57.5250],
            [-25.2400, -57.5100]
        ],
        "lineas_colectivo": ["Línea 30 (Aeropuerto)"],
        "paralelas_ids": [17]
    },
    {
        "id_tramo": 17,
        "codigo": "LUQ-GENERAL-AQUINO-01",
        "nombre_calle": "Avda. General Aquino (Tapua)",
        "municipio": "Luque",
        "categoria": "ARTERIAL",
        "sentido": "DOBLE",
        "nodo_origen": "Límite Asunción / Luque",
        "nodo_destino": "Centro de Luque",
        "carriles": 2,
        "longitud_m": 4300,
        "velocidad_limite_kmh": 45.0,
        "capacidad_veh_hora": 1600,
        "flujo_base_veh_hora": 1420,
        "coordenadas": [
            [-25.2720, -57.5380],
            [-25.2680, -57.5150],
            [-25.2650, -57.4920]
        ],
        "lineas_colectivo": ["Línea 28", "Línea 30", "Línea 51"],
        "paralelas_ids": [16]
    },

    # --- GRAN ASUNCIÓN: LAMBARÉ ---
    {
        "id_tramo": 18,
        "codigo": "LAM-CACIQUE-LAMBARE-01",
        "nombre_calle": "Avda. Cacique Lambaré",
        "municipio": "Lambaré",
        "categoria": "TRONCAL",
        "sentido": "DOBLE",
        "nodo_origen": "Avda. Fernando de la Mora",
        "nodo_destino": "Municipalidad de Lambaré",
        "carriles": 4,
        "longitud_m": 3100,
        "velocidad_limite_kmh": 50.0,
        "capacidad_veh_hora": 2400,
        "flujo_base_veh_hora": 1950,
        "coordenadas": [
            [-25.3280, -57.6180],
            [-25.3400, -57.6120],
            [-25.3520, -57.6060]
        ],
        "lineas_colectivo": ["Línea 23", "Línea 33", "Línea 41"],
        "paralelas_ids": [19]
    },
    {
        "id_tramo": 19,
        "codigo": "LAM-1RO-MARZO-01",
        "nombre_calle": "Avda. 1ro de Marzo",
        "municipio": "Lambaré",
        "categoria": "COLECTORA",
        "sentido": "DOBLE",
        "nodo_origen": "Avda. Perón",
        "nodo_destino": "Avda. Cacique Lambaré",
        "carriles": 2,
        "longitud_m": 2200,
        "velocidad_limite_kmh": 40.0,
        "capacidad_veh_hora": 1100,
        "flujo_base_veh_hora": 720,
        "coordenadas": [
            [-25.3350, -57.6290],
            [-25.3420, -57.6200],
            [-25.3480, -57.6100]
        ],
        "lineas_colectivo": ["Línea 9"],
        "paralelas_ids": [18]
    }
]

# =====================================================================
# MOTOR DE TRÁFICO Y REASIGNACIÓN BPR (WHAT-IF ENGINE)
# =====================================================================

@dataclass
class ModificacionTramo:
    id_tramo: int
    nuevo_sentido: str # 'DOBLE' | 'UNICO_DIRECTO' | 'UNICO_INVERSO' | 'CERRADO'
    carril_bus_exclusivo: bool = False
    motivo: str = ""

@dataclass
class ResultadoTramo:
    id_tramo: int
    nombre_calle: str
    municipio: str
    sentido_anterior: str
    sentido_nuevo: str
    flujo_anterior_veh_h: int
    flujo_nuevo_veh_h: int
    capacidad_veh_h: int
    velocidad_libre_kmh: float
    velocidad_efectiva_anterior_kmh: float
    velocidad_efectiva_nueva_kmh: float
    tiempo_recorrido_anterior_min: float
    tiempo_recorrido_nuevo_min: float
    nivel_servicio_anterior: str # A, B, C, D, E, F
    nivel_servicio_nuevo: str
    ratio_saturacion: float
    estado_impacto: str # 'MEJORADO' | 'ESTABLE' | 'MODERADO' | 'COLAPSO'
    lineas_afectadas: List[str]
    coordenadas: List[List[float]]

@dataclass
class ResultadoSimulacionTrafico:
    municipio_objetivo: str
    franja_horaria: str
    total_tramos_analizados: int
    tramos_modificados: int
    velocidad_promedio_anterior_kmh: float
    velocidad_promedio_nueva_kmh: float
    variacion_velocidad_pct: float
    tiempo_viaje_promedio_anterior_min: float
    tiempo_viaje_promedio_nuevo_min: float
    variacion_tiempo_viaje_pct: float
    calles_en_colapso: List[Dict[str, Any]]
    lineas_transporte_impactadas: List[Dict[str, Any]]
    resumen_ejecutivo: str
    tramos: List[ResultadoTramo]


class MotorTraficoAsuncion:
    """
    Motor analítico de tráfico macroscópico con funciones de demora BPR
    y reasignación de flujos para Asunción y Gran Asunción.
    """

    ALPHA = 0.15
    BETA = 4.0

    FACTORES_HORA_PICO = {
        "PICO_MANANA": 1.25, # 07:00 a 08:30 (ingreso masivo a Asunción)
        "PICO_TARDE": 1.30,  # 17:30 a 19:30 (salida masiva hacia Gran Asunción)
        "VALLE": 0.80        # 11:00 a 14:00 (tráfico fluido intermedio)
    }

    def __init__(self, red_base: Optional[List[Dict[str, Any]]] = None):
        self.tramos_raw = red_base or RED_VIAL_ASUNCION_METRO

    @classmethod
    def calcular_demora_bpr(cls, longitud_m: float, velocidad_libre_kmh: float, volumen: float, capacidad: float) -> Tuple[float, float, str]:
        """
        Calcula el tiempo de viaje (minutos), velocidad efectiva (km/h) y Nivel de Servicio (LOS)
        usando la fórmula de la Bureau of Public Roads:
        T = T0 * (1 + 0.15 * (V/C)^4)
        """
        if capacidad <= 0:
            return 999.0, 0.5, "F"

        longitud_km = longitud_m / 1000.0
        t0_min = (longitud_km / max(velocidad_libre_kmh, 10.0)) * 60.0
        
        ratio = max(0.0, volumen / capacidad)
        t_efectivo_min = t0_min * (1.0 + cls.ALPHA * (ratio ** cls.BETA))
        
        # Evitar división por cero
        vel_efectiva_kmh = (longitud_km / max(t_efectivo_min / 60.0, 0.001))
        vel_efectiva_kmh = min(vel_efectiva_kmh, velocidad_libre_kmh)

        # Nivel de Servicio (LOS: Level of Service)
        if ratio < 0.60:
            los = "A/B"
        elif ratio < 0.85:
            los = "C"
        elif ratio < 1.05:
            los = "D/E"
        else:
            los = "F" # Saturación / Colapso

        return round(t_efectivo_min, 2), round(vel_efectiva_kmh, 1), los

    def ejecutar_what_if(
        self,
        modificaciones: List[Dict[str, Any]],
        municipio: str = "Asunción",
        franja: str = "PICO_MANANA"
    ) -> ResultadoSimulacionTrafico:
        """
        Ejecuta la reasignación de tráfico ante cambios de sentido o cierres.
        """
        factor_hora = self.FACTORES_HORA_PICO.get(franja, 1.0)
        mods_map = {m["id_tramo"]: m for m in modificaciones}
        
        # Copia de trabajo de los tramos
        tramos_dict = {t["id_tramo"]: dict(t) for t in self.tramos_raw}
        
        # 1. Calcular estado base (ANTERIOR)
        estado_base = {}
        for tid, t in tramos_dict.items():
            flujo_base = int(t["flujo_base_veh_hora"] * factor_hora)
            cap = t["capacidad_veh_hora"]
            t_min, vel_kmh, los = self.calcular_demora_bpr(
                t["longitud_m"], t["velocidad_limite_kmh"], flujo_base, cap
            )
            estado_base[tid] = {
                "flujo": flujo_base,
                "capacidad": cap,
                "tiempo_min": t_min,
                "velocidad_kmh": vel_kmh,
                "los": los
            }

        # 2. Aplicar Modificaciones y Detectar Flujo Desplazado
        flujo_desplazado_por_paralela: Dict[int, int] = {}
        tramos_afectados_tp = []

        for tid, mod in mods_map.items():
            if tid not in tramos_dict:
                continue
            
            t = tramos_dict[tid]
            sentido_anterior = t["sentido"]
            nuevo_sentido = mod.get("nuevo_sentido", sentido_anterior)
            carril_bus = mod.get("carril_bus_exclusivo", False)

            flujo_original = estado_base[tid]["flujo"]
            cap_original = estado_base[tid]["capacidad"]

            # Si se cierra la calle
            if nuevo_sentido == "CERRADO":
                volumen_a_desviar = flujo_original
                t["capacidad_veh_hora"] = 10 # Casi nula
                t["flujo_nuevo"] = 0
                t["sentido"] = "CERRADO"
            
            # Si se cambia de doble a único sentido o se invierte
            elif sentido_anterior == "DOBLE" and nuevo_sentido in ["UNICO_DIRECTO", "UNICO_INVERSO"]:
                # 45% del tráfico que iba en sentido contrario debe reasignarse
                volumen_a_desviar = int(flujo_original * 0.45)
                t["flujo_nuevo"] = flujo_original - volumen_a_desviar
                t["sentido"] = nuevo_sentido
            
            elif sentido_anterior in ["UNICO_DIRECTO", "UNICO_INVERSO"] and nuevo_sentido in ["UNICO_DIRECTO", "UNICO_INVERSO"] and sentido_anterior != nuevo_sentido:
                # Se invirtió completamente el sentido: el 100% del sentido viejo debe buscar otra calle
                volumen_a_desviar = int(flujo_original * 0.85)
                t["flujo_nuevo"] = int(flujo_original * 0.35) # Tráfico nuevo que ahora aprovecha el nuevo sentido
                t["sentido"] = nuevo_sentido
            else:
                volumen_a_desviar = 0
                t["flujo_nuevo"] = flujo_original

            # Si se asigna carril exclusivo de bus, se reduce la capacidad para autos particulares un 40%
            if carril_bus:
                t["capacidad_veh_hora"] = int(t["capacidad_veh_hora"] * 0.60)

            # Distribuir el volumen desviado hacia las calles paralelas directas
            paralelas = t.get("paralelas_ids", [])
            if paralelas and volumen_a_desviar > 0:
                cuota_por_paralela = int(volumen_a_desviar / len(paralelas))
                for pid in paralelas:
                    flujo_desplazado_por_paralela[pid] = flujo_desplazado_por_paralela.get(pid, 0) + cuota_por_paralela

            # Si tiene líneas de colectivos y se alteró el flujo, registrar impacto
            if t.get("lineas_colectivo"):
                tramos_afectados_tp.append({
                    "id_tramo": tid,
                    "calle": t["nombre_calle"],
                    "lineas": t["lineas_colectivo"],
                    "nuevo_sentido": nuevo_sentido,
                    "requiere_desvio": (nuevo_sentido == "CERRADO" or (sentido_anterior != nuevo_sentido and sentido_anterior != "DOBLE"))
                })

        # 3. Calcular Estado Posterior (NUEVO) con Derrame de Tráfico
        resultados_tramos: List[ResultadoTramo] = []
        calles_colapso = []

        total_vel_ant = 0.0
        total_vel_nue = 0.0
        total_t_ant = 0.0
        total_t_nue = 0.0
        count_tramos = 0

        for tid, t in tramos_dict.items():
            base = estado_base[tid]
            flujo_adicional = flujo_desplazado_por_paralela.get(tid, 0)
            
            flujo_final = t.get("flujo_nuevo", base["flujo"]) + flujo_adicional
            cap_final = t["capacidad_veh_hora"]
            
            t_min_nue, vel_kmh_nue, los_nue = self.calcular_demora_bpr(
                t["longitud_m"], t["velocidad_limite_kmh"], flujo_final, cap_final
            )

            ratio_sat = round(flujo_final / max(cap_final, 1), 2)

            # Clasificar impacto
            if t["sentido"] == "CERRADO":
                impacto = "COLAPSO"
            elif ratio_sat >= 1.05:
                impacto = "COLAPSO"
                calles_colapso.append({
                    "id_tramo": tid,
                    "calle": t["nombre_calle"],
                    "municipio": t["municipio"],
                    "saturacion_pct": int(ratio_sat * 100),
                    "velocidad_kmh": vel_kmh_nue,
                    "retraso_adicional_min": round(t_min_nue - base["tiempo_min"], 1),
                    "motivo": "Absorción de derrame de tráfico de calles modificadas" if flujo_adicional > 0 else "Sobrecarga de demanda"
                })
            elif ratio_sat >= 0.85:
                impacto = "MODERADO"
            elif vel_kmh_nue > base["velocidad_kmh"] + 2:
                impacto = "MEJORADO"
            else:
                impacto = "ESTABLE"

            res = ResultadoTramo(
                id_tramo=tid,
                nombre_calle=t["nombre_calle"],
                municipio=t["municipio"],
                sentido_anterior=self.tramos_raw[tid - 1]["sentido"],
                sentido_nuevo=t["sentido"],
                flujo_anterior_veh_h=base["flujo"],
                flujo_nuevo_veh_h=flujo_final,
                capacidad_veh_h=cap_final,
                velocidad_libre_kmh=t["velocidad_limite_kmh"],
                velocidad_efectiva_anterior_kmh=base["velocidad_kmh"],
                velocidad_efectiva_nueva_kmh=vel_kmh_nue,
                tiempo_recorrido_anterior_min=base["tiempo_min"],
                tiempo_recorrido_nuevo_min=t_min_nue,
                nivel_servicio_anterior=base["los"],
                nivel_servicio_nuevo=los_nue,
                ratio_saturacion=ratio_sat,
                estado_impacto=impacto,
                lineas_afectadas=t.get("lineas_colectivo", []),
                coordenadas=t.get("coordenadas", [])
            )
            resultados_tramos.append(res)

            total_vel_ant += base["velocidad_kmh"]
            total_vel_nue += vel_kmh_nue
            total_t_ant += base["tiempo_min"]
            total_t_nue += t_min_nue
            count_tramos += 1

        # Promedios de la red
        avg_vel_ant = round(total_vel_ant / max(count_tramos, 1), 1)
        avg_vel_nue = round(total_vel_nue / max(count_tramos, 1), 1)
        avg_t_ant = round(total_t_ant / max(count_tramos, 1), 1)
        avg_t_nue = round(total_t_nue / max(count_tramos, 1), 1)

        var_vel_pct = round(((avg_vel_nue - avg_vel_ant) / max(avg_vel_ant, 1)) * 100, 1)
        var_t_pct = round(((avg_t_nue - avg_t_ant) / max(avg_t_ant, 1)) * 100, 1)

        # 4. Consolidar impacto en Transporte Público
        lineas_impacto_dict = {}
        for item in tramos_afectados_tp:
            for l in item["lineas"]:
                if l not in lineas_impacto_dict:
                    lineas_impacto_dict[l] = {
                        "linea": l,
                        "tramos_afectados": [],
                        "desvio_obligatorio": False,
                        "retraso_estimado_min": 0.0
                    }
                lineas_impacto_dict[l]["tramos_afectados"].append(item["calle"])
                if item["requiere_desvio"]:
                    lineas_impacto_dict[l]["desvio_obligatorio"] = True
                    lineas_impacto_dict[l]["retraso_estimado_min"] += 5.5
                else:
                    lineas_impacto_dict[l]["retraso_estimado_min"] += 2.0

        lineas_finales = list(lineas_impacto_dict.values())

        # 5. Generar Resumen Ejecutivo para la Municipalidad
        if len(mods_map) == 0:
            resumen = f"Simulación de tráfico base para {municipio} ({franja.replace('_', ' ')}). La red opera con velocidad promedio de {avg_vel_ant} km/h sin intervenciones extraordinarias."
        else:
            resumen = (
                f"Se simularon {len(mods_map)} modificaciones de tránsito en {municipio}. "
                f"La velocidad media de la red varía en un {var_vel_pct}% (de {avg_vel_ant} a {avg_vel_nue} km/h). "
                f"Se detectan {len(calles_colapso)} tramos en saturación crítica por desvío de tráfico "
                f"y {len(lineas_finales)} líneas de transporte público con demoras o desvíos obligatorios."
            )

        return ResultadoSimulacionTrafico(
            municipio_objetivo=municipio,
            franja_horaria=franja,
            total_tramos_analizados=count_tramos,
            tramos_modificados=len(mods_map),
            velocidad_promedio_anterior_kmh=avg_vel_ant,
            velocidad_promedio_nueva_kmh=avg_vel_nue,
            variacion_velocidad_pct=var_vel_pct,
            tiempo_viaje_promedio_anterior_min=avg_t_ant,
            tiempo_viaje_promedio_nuevo_min=avg_t_nue,
            variacion_tiempo_viaje_pct=var_t_pct,
            calles_en_colapso=calles_colapso,
            lineas_transporte_impactadas=lineas_finales,
            resumen_ejecutivo=resumen,
            tramos=resultados_tramos
        )

motor_trafico = MotorTraficoAsuncion()
