from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ─────────────── Empresa ───────────────
class EmpresaBase(BaseModel):
    nombre: str
    ruc: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    estado: bool = True


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaResponse(EmpresaBase):
    id_empresa: int
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────── Linea ───────────────
class LineaBase(BaseModel):
    codigo: str
    numero_linea: Optional[str] = None
    nombre_comercial: Optional[str] = None
    descripcion: Optional[str] = None
    color_hex: Optional[str] = "#3B82F6"
    estado: bool = True
    id_empresa: Optional[int] = None


class LineaCreate(LineaBase):
    pass


class LineaResponse(LineaBase):
    id_linea: int
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────── Ruta ───────────────
class RutaBase(BaseModel):
    id_linea: int
    sentido: str   # IDA | VUELTA
    nombre: Optional[str] = None
    distancia_km: Optional[float] = None
    tiempo_ciclo_min: Optional[float] = None


class RutaCreate(RutaBase):
    pass


class RutaResponse(RutaBase):
    id_ruta: int

    class Config:
        from_attributes = True


# ─────────────── Paradero ───────────────
class ParaderoBase(BaseModel):
    nombre: str
    tipo: str   # INICIO | INTERMEDIO | TERMINAL
    orden_ruta: Optional[int] = None
    distancia_desde_inicio_m: Optional[float] = None
    id_ruta: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


class ParaderoCreate(ParaderoBase):
    pass


class ParaderoResponse(ParaderoBase):
    id_paradero: int
    estado: bool = True

    class Config:
        from_attributes = True


# ─────────────── Bus ───────────────
class BusBase(BaseModel):
    interno: Optional[str] = None
    placa: Optional[str] = None
    capacidad: int = 45
    estado: str = "ACTIVO"
    modelo: Optional[str] = None
    anio: Optional[int] = None
    id_empresa: Optional[int] = None


class BusCreate(BusBase):
    pass


class BusResponse(BusBase):
    id_bus: int
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────── PosicionGPS ───────────────
class PosicionGPSBase(BaseModel):
    id_bus: int
    lat: float
    lon: float
    velocidad: Optional[float] = None
    rumbo: Optional[int] = None
    fuente: str = "AVL"
    id_simulacion: Optional[int] = None


class PosicionGPSCreate(PosicionGPSBase):
    pass


class PosicionGPSResponse(PosicionGPSBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ─────────────── Simulacion ───────────────
class SimulacionParametros(BaseModel):
    id_linea: int
    headway_min: float = 8.0
    velocidad_kmh: float = 25.0
    num_buses: int = 5
    duracion_sim_min: float = 120.0
    tasa_pasajeros_por_min: float = 2.0
    tiempo_parada_base_min: float = 0.5
    semilla_aleatoria: Optional[int] = None


class SimulacionCreate(BaseModel):
    nombre: str
    parametros: SimulacionParametros


class SimulacionResponse(BaseModel):
    id_simulacion: int
    nombre: str
    estado: str
    parametros: Optional[dict] = None
    resultado_resumen: Optional[dict] = None
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─────────────── KPI ───────────────
class KPIHeadway(BaseModel):
    id_linea: int
    headway_promedio_min: float
    headway_std_min: float
    headway_min_min: float
    headway_max_min: float
    regularidad_pct: float
    num_observaciones: int


class KPIBunching(BaseModel):
    id_linea: int
    buses_bunching: int
    total_buses: int
    pct_bunching: float
    umbral_usado: float


class KPIResumen(BaseModel):
    linea: str
    headway_promedio: float
    regularidad: float
    velocidad_comercial: float
    pct_bunching: float
    total_buses_activos: int
    total_pasajeros_estimados: int


# ─────────────── Evento Operacional ───────────────
class EventoOperacionalResponse(BaseModel):
    id: int
    tipo_evento: str
    id_bus: int
    id_paradero: Optional[int]
    timestamp: datetime
    descripcion: Optional[str]

    class Config:
        from_attributes = True


# ─────────────── WebSocket Messages ───────────────
class WSMessage(BaseModel):
    tipo: str
    datos: Any
    timestamp: Optional[str] = None
