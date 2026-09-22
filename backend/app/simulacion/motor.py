"""
Motor de Microsimulación de Transporte Público
Basado en SimPy (Discrete Event Simulation)

Modela:
- Buses como agentes que recorren rutas
- Paraderos con colas de pasajeros
- Cálculo de headways y regularidad
- Detección de bunching
"""

import simpy
import numpy as np
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ConfigParadero:
    id_paradero: int
    nombre: str
    orden: int
    distancia_m: float
    tipo: str = "INTERMEDIO"  # INICIO | INTERMEDIO | TERMINAL
    tasa_llegada_pax: float = 1.0  # pasajeros/minuto


@dataclass
class ConfigRuta:
    id_ruta: int
    id_linea: int
    nombre: str
    paraderos: List[ConfigParadero]
    distancia_total_km: float


@dataclass
class ConfigSimulacion:
    id_linea: int
    nombre_linea: str
    ruta: ConfigRuta
    num_buses: int = 5
    headway_programado_min: float = 8.0
    velocidad_kmh: float = 25.0
    capacidad_bus: int = 45
    duracion_sim_min: float = 120.0
    tasa_pasajeros_global: float = 2.0
    tiempo_parada_base_min: float = 0.5
    tiempo_por_pasajero_min: float = 0.05
    semilla: Optional[int] = None


@dataclass
class EstadoBus:
    id_bus: int
    interno: str
    posicion_m: float = 0.0
    velocidad_kmh: float = 0.0
    pasajeros_abordo: int = 0
    paradero_actual: Optional[int] = None
    en_paradero: bool = False
    tiempo_sim: float = 0.0
    total_ascensos: int = 0
    total_descensos: int = 0
    historial_arribo: List[Dict] = field(default_factory=list)


@dataclass
class ResultadoSimulacion:
    id_simulacion: int
    nombre: str
    estado: str
    duracion_sim_min: float
    
    # KPIs
    headway_promedio_min: float = 0.0
    headway_std_min: float = 0.0
    regularidad_pct: float = 0.0
    pct_bunching: float = 0.0
    velocidad_comercial_kmh: float = 0.0
    total_pasajeros_transportados: int = 0
    total_eventos: int = 0
    
    # Series temporales
    posiciones: List[Dict] = field(default_factory=list)
    eventos: List[Dict] = field(default_factory=list)
    headways_por_paradero: Dict[int, List[float]] = field(default_factory=dict)
    estados_buses: List[Dict] = field(default_factory=list)


class MotorSimulacion:
    """
    Motor de simulación de eventos discretos para transporte público.
    Utiliza SimPy para modelar el sistema como agentes concurrentes.
    """

    def __init__(self, config: ConfigSimulacion, db=None, billetaje_db=None):
        self.config = config
        self.env = simpy.Environment()
        self.db = db
        self.billetaje_db = billetaje_db
        self.rng = np.random.default_rng(config.semilla)
        
        # Inicialización de estado (Siempre debe ocurrir en __init__)
        self.buses: Dict[int, EstadoBus] = {}
        self.colas_paraderos: Dict[int, simpy.Container] = {}
        self.ultimo_arribo_por_paradero: Dict[int, float] = {}
        self.headways_registrados: Dict[int, List[float]] = {}
        self.posiciones_registradas: List[Dict] = []
        self.eventos_registrados: List[Dict] = []
        self.callback_progreso: Optional[Callable] = None
        
        # Cargar demanda real si está disponible
        self.demanda_real = {}
        if self.billetaje_db:
            self._cargar_demanda_real()
            
        self._inicializar_recursos()

    def _cargar_demanda_real(self):
        """Pre-carga la demanda desde Billetaje para la ventana de tiempo simulada."""
        try:
            from datetime import timedelta
            logger.info(f"📊 Extrayendo demanda real para ruta {self.config.id_linea}...")
            # Definir ventana (demo: últimas 24h o fecha específica)
            fin = datetime.now()
            inicio = fin - timedelta(hours=self.config.duracion_sim_min / 60)
            
            from app.services.billetaje_service import billetaje_service
            self.demanda_real = billetaje_service.get_demanda_historica(
                self.billetaje_db, 
                self.config.id_linea, 
                inicio, 
                fin
            )
            logger.info(f"✅ Cargados {len(self.demanda_real)} registros de demanda real.")
        except Exception as e:
            logger.error(f"⚠️ No se pudo cargar demanda real: {e}")
            self.demanda_real = []

    def _inicializar_recursos(self):
        """Inicializa colas de paraderos y estructuras de datos."""
        for paradero in self.config.ruta.paraderos:
            self.colas_paraderos[paradero.id_paradero] = simpy.Container(
                self.env, capacity=200, init=0
            )
            self.ultimo_arribo_por_paradero[paradero.id_paradero] = -999.0
            self.headways_registrados[paradero.id_paradero] = []

    def _tiempo_viaje_entre_paraderos(self, dist_m: float) -> float:
        """Calcula el tiempo de viaje con variabilidad (congestión simulada)."""
        v_base = self.config.velocidad_kmh
        # Variabilidad ±20% por congestión
        factor_congestion = self.rng.uniform(0.8, 1.2)
        v_real = v_base * factor_congestion
        tiempo_min = (dist_m / 1000) / v_real * 60
        return max(0.1, tiempo_min)

    def _tiempo_en_paradero(self, pasajeros_suben: int, pasajeros_bajan: int) -> float:
        """Calcula el tiempo de parada según pasajeros."""
        t_base = self.config.tiempo_parada_base_min
        t_pax = (pasajeros_suben + pasajeros_bajan) * self.config.tiempo_por_pasajero_min
        return t_base + t_pax

    def _registrar_evento(self, tipo: str, id_bus: int, id_paradero: Optional[int],
                           descripcion: str, metadata: Optional[Dict] = None):
        self.eventos_registrados.append({
            "tipo_evento": tipo,
            "id_bus": id_bus,
            "id_paradero": id_paradero,
            "tiempo_sim": self.env.now,
            "descripcion": descripcion,
            "metadata": metadata or {},
        })

    def _proceso_bus(self, id_bus: int):
        """Proceso SimPy que modela el comportamiento de un bus."""
        estado = self.buses[id_bus]
        paraderos = self.config.ruta.paraderos
        num_paraderos = len(paraderos)
        if num_paraderos < 2:
            return
        
        while True:
            # Recorrer todos los paraderos de la ruta
            for i, paradero in enumerate(paraderos):
                # Tiempo de viaje desde posición actual
                if i == 0:
                    dist = paraderos[0].distancia_m
                else:
                    dist = paraderos[i].distancia_m - paraderos[i-1].distancia_m
                
                t_viaje = self._tiempo_viaje_entre_paraderos(max(dist, 100))
                
                # Registrar posición durante el viaje
                yield self.env.timeout(t_viaje / 2)
                
                pos_relativa = paraderos[i].distancia_m - dist / 2
                self.posiciones_registradas.append({
                    "id_bus": id_bus,
                    "interno": estado.interno,
                    "posicion_m": pos_relativa,
                    "tiempo_sim": self.env.now,
                    "pasajeros_abordo": estado.pasajeros_abordo,
                    "velocidad_kmh": estado.velocidad_kmh,
                })
                
                yield self.env.timeout(t_viaje / 2)
                
                # ARRIBO AL PARADERO
                estado.paradero_actual = paradero.id_paradero
                estado.en_paradero = True
                estado.posicion_m = paradero.distancia_m
                estado.tiempo_sim = self.env.now
                
                # Calcular headway
                t_ultimo = self.ultimo_arribo_por_paradero[paradero.id_paradero]
                if t_ultimo > 0:
                    headway = self.env.now - t_ultimo
                    self.headways_registrados[paradero.id_paradero].append(headway)
                    
                    # Detección de bunching
                    if headway < self.config.headway_programado_min * 0.5:
                        self._registrar_evento(
                            "BUNCHING", id_bus, paradero.id_paradero,
                            f"Bus {estado.interno}: headway {headway:.1f} min < umbral",
                            {"headway": headway, "umbral": self.config.headway_programado_min * 0.5}
                        )
                
                self.ultimo_arribo_por_paradero[paradero.id_paradero] = self.env.now
                
                self._registrar_evento(
                    "ARRIBO", id_bus, paradero.id_paradero,
                    f"Bus {estado.interno} arriba a {paradero.nombre}",
                    {"paradero": paradero.nombre, "pax_abordo": estado.pasajeros_abordo}
                )
                
                # OPERACIÓN EN PARADERO: descenso y ascenso
                # Pasajeros que bajan (~30% de los abordo, excepto en terminal)
                if paradero.tipo == "TERMINAL" or i == num_paraderos - 1:
                    bajan = estado.pasajeros_abordo
                else:
                    bajan = int(estado.pasajeros_abordo * self.rng.uniform(0.1, 0.4))
                
                bajan = min(bajan, estado.pasajeros_abordo)
                estado.pasajeros_abordo -= bajan
                estado.total_descensos += bajan
                
                # Pasajeros que suben (de la cola/demanda)
                if paradero.tipo != "TERMINAL":
                    demanda_local = self.rng.poisson(paradero.tasa_llegada_pax * t_viaje)
                    espacio_libre = self.config.capacidad_bus - estado.pasajeros_abordo
                    suben = min(demanda_local, espacio_libre)
                    estado.pasajeros_abordo += suben
                    estado.total_ascensos += suben
                else:
                    suben = 0
                    estado.pasajeros_abordo = 0  # Terminal: todos bajan
                
                # Tiempo en paradero
                t_parada = self._tiempo_en_paradero(suben, bajan)
                yield self.env.timeout(t_parada)
                
                estado.en_paradero = False
                
                self._registrar_evento(
                    "PARTIDA", id_bus, paradero.id_paradero,
                    f"Bus {estado.interno} parte de {paradero.nombre}",
                    {"suben": suben, "bajan": bajan, "pax_total": estado.pasajeros_abordo}
                )
                
                # Posición actualizada
                self.posiciones_registradas.append({
                    "id_bus": id_bus,
                    "interno": estado.interno,
                    "posicion_m": paradero.distancia_m,
                    "tiempo_sim": self.env.now,
                    "pasajeros_abordo": estado.pasajeros_abordo,
                    "velocidad_kmh": self.config.velocidad_kmh,
                    "en_paradero": False,
                })

    def _proceso_generador_pasajeros(self, id_paradero: int, tasa: float):
        """Genera pasajeros según proceso de Poisson en cada paradero."""
        while True:
            inter_arrival = self.rng.exponential(1.0 / tasa)
            yield self.env.timeout(inter_arrival)

    def ejecutar(self, id_simulacion: int = 0) -> ResultadoSimulacion:
        """Ejecuta la simulación completa y retorna los resultados."""
        logger.info(f"🚌 Iniciando simulación: {self.config.nombre_linea}")
        
        # Crear buses con desfase inicial (headway programado)
        for i in range(self.config.num_buses):
            id_bus = i + 1
            estado = EstadoBus(
                id_bus=id_bus,
                interno=f"BUS-{i+1:03d}",
                velocidad_kmh=self.config.velocidad_kmh,
            )
            self.buses[id_bus] = estado
            
            # Desfase inicial entre buses
            desfase = i * self.config.headway_programado_min
            
            # Proceso con desfase
            def make_process(bid, desfase_min):
                def proceso():
                    yield self.env.timeout(desfase_min)
                    yield from self._proceso_bus(bid)
                return proceso
            
            self.env.process(make_process(id_bus, desfase)())
        
        # Ejecutar simulación
        self.env.run(until=self.config.duracion_sim_min)
        
        logger.info(f"✅ Simulación completada. Eventos: {len(self.eventos_registrados)}")
        
        # Calcular KPIs
        return self._calcular_resultado(id_simulacion)

    def _calcular_resultado(self, id_simulacion: int) -> ResultadoSimulacion:
        """Calcula KPIs y construye el objeto de resultado."""
        
        # Headway promedio (todos los paraderos)
        todos_headways = []
        for hw_list in self.headways_registrados.values():
            todos_headways.extend(hw_list)
        
        hw_promedio = float(np.mean(todos_headways)) if todos_headways else 0.0
        hw_std = float(np.std(todos_headways)) if todos_headways else 0.0
        
        # Regularidad: % headways dentro del ±30% del programado
        if todos_headways:
            umbral = self.config.headway_programado_min * 0.3
            regulares = sum(
                1 for h in todos_headways
                if abs(h - self.config.headway_programado_min) <= umbral
            )
            regularidad = regulares / len(todos_headways) * 100
        else:
            regularidad = 0.0
        
        # Bunching: eventos de bunching / total arrivals
        arribs = [e for e in self.eventos_registrados if e["tipo_evento"] == "ARRIBO"]
        bunchings = [e for e in self.eventos_registrados if e["tipo_evento"] == "BUNCHING"]
        pct_bunching = len(bunchings) / max(len(arribs), 1) * 100
        
        # Pasajeros totales
        total_pax = sum(b.total_ascensos for b in self.buses.values())
        
        resultado = ResultadoSimulacion(
            id_simulacion=id_simulacion,
            nombre=self.config.nombre_linea,
            estado="COMPLETADO",
            duracion_sim_min=self.config.duracion_sim_min,
            headway_promedio_min=round(hw_promedio, 2),
            headway_std_min=round(hw_std, 2),
            regularidad_pct=round(regularidad, 1),
            pct_bunching=round(pct_bunching, 1),
            velocidad_comercial_kmh=self.config.velocidad_kmh,
            total_pasajeros_transportados=total_pax,
            total_eventos=len(self.eventos_registrados),
            posiciones=self.posiciones_registradas[-500:],  # últimas 500 posiciones
            eventos=self.eventos_registrados[-200:],
            headways_por_paradero=self.headways_registrados,
            estados_buses=[
                {
                    "id_bus": b.id_bus,
                    "interno": b.interno,
                    "total_ascensos": b.total_ascensos,
                    "total_descensos": b.total_descensos,
                }
                for b in self.buses.values()
            ],
        )
        
        return resultado
