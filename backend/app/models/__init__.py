from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime


class Empresa(Base):
    __tablename__ = "empresas"
    id_empresa = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    codigo_eot = Column(String(20), unique=True, index=True) # ID en BD CID (public.eots)
    ruc = Column(String(20))
    id_consorcio = Column(Integer, ForeignKey("consorcios.id_consorcio"), nullable=True)
    estado = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    buses = relationship("Bus", back_populates="empresa")
    consorcio = relationship("Consorcio", back_populates="empresas")

class Consorcio(Base):
    __tablename__ = "consorcios"
    id_consorcio = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    id_externo_cid = Column(String(50), nullable=True) # Mapping a gestion_uf
    
    empresas = relationship("Empresa", back_populates="consorcio")
    unidades_funcionales = relationship("UnidadFuncional", back_populates="consorcio")

class UnidadFuncional(Base):
    __tablename__ = "unidades_funcionales"
    id_uf = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    id_consorcio = Column(Integer, ForeignKey("consorcios.id_consorcio"))
    id_externo_cid = Column(String(50), nullable=True) # Mapping a gestion_uf
    
    consorcio = relationship("Consorcio", back_populates="unidades_funcionales")
    composiciones = relationship("ComposicionUf", back_populates="unidad_funcional")

class ComposicionUf(Base):
    __tablename__ = "composicion_uf"
    id_comp_uf = Column(Integer, primary_key=True, index=True)
    id_uf = Column(Integer, ForeignKey("unidades_funcionales.id_uf"))
    id_linea = Column(Integer, ForeignKey("lineas.id_linea"))
    
    unidad_funcional = relationship("UnidadFuncional", back_populates="composiciones")
    linea = relationship("Linea", back_populates="en_unidades")

class Linea(Base):
    __tablename__ = "lineas"
    id_linea = Column(Integer, primary_key=True, index=True)
    numero_linea = Column(String(20), nullable=False, unique=True)
    nombre_comercial = Column(String(200))
    identificador_troncal = Column(String(100))
    color_hex = Column(String(7), default="#3B82F6")
    estado = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    rutas = relationship("LineaRutaCatalogo", back_populates="linea")
    en_unidades = relationship("ComposicionUf", back_populates="linea")

class LineaRutaCatalogo(Base):
    __tablename__ = "linea_ruta_catalogo"
    id_linea_ruta_catalogo = Column(Integer, primary_key=True, index=True)
    id_linea = Column(Integer, ForeignKey("lineas.id_linea"))
    ruta_hex = Column(String(50), nullable=False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    
    linea = relationship("Linea", back_populates="rutas")


class Ruta(Base):
    __tablename__ = "rutas"
    id_ruta = Column(Integer, primary_key=True, index=True)
    id_linea = Column(Integer, ForeignKey("lineas.id_linea"))
    sentido = Column(String(50))   # IDA | VUELTA | CIRCULAR | CIRCULAR IDA | etc.
    nombre = Column(String(200))
    geom = Column(Geometry("LINESTRING", srid=4326))
    id_externo_cid = Column(String(100), nullable=True) # Mapping a public.catalogo_rutas (ruta_hex)
    distancia_km = Column(Float)
    tiempo_ciclo_min = Column(Float)

    # Relación opcional con Linea si se usa el esquema local
    linea = relationship("Linea") 
    paraderos = relationship("Paradero", back_populates="ruta")


class Paradero(Base):
    __tablename__ = "paraderos"

    id_paradero = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200))
    tipo = Column(String(20))   # INICIO | INTERMEDIO | TERMINAL
    geom = Column(Geometry("POINT", srid=4326))
    orden_ruta = Column(Integer)
    distancia_desde_inicio_m = Column(Float)
    id_ruta = Column(Integer, ForeignKey("rutas.id_ruta"))
    estado = Column(Boolean, default=True)

    ruta = relationship("Ruta", back_populates="paraderos")


class Bus(Base):
    __tablename__ = "buses"

    id_bus = Column(Integer, primary_key=True, index=True)
    interno = Column(String(20))
    placa = Column(String(20))
    capacidad = Column(Integer, default=45)
    estado = Column(String(20), default="ACTIVO")  # ACTIVO | INACTIVO | MANTENIMIENTO
    modelo = Column(String(100))
    anio = Column(Integer)
    id_empresa = Column(Integer, ForeignKey("empresas.id_empresa"))
    creado_en = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="buses")
    posiciones = relationship("PosicionGPS", back_populates="bus")
    eventos = relationship("EventoOperacional", back_populates="bus")


class PosicionGPS(Base):
    __tablename__ = "posiciones_gps"

    id = Column(Integer, primary_key=True, index=True)
    id_bus = Column(Integer, ForeignKey("buses.id_bus"))
    geom = Column(Geometry("POINT", srid=4326))
    lat = Column(Float)
    lon = Column(Float)
    velocidad = Column(Float)
    rumbo = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    fuente = Column(String(20), default="AVL")   # AVL | SIMULACION
    id_simulacion = Column(Integer, ForeignKey("simulaciones.id_simulacion"), nullable=True)

    bus = relationship("Bus", back_populates="posiciones")


class EventoOperacional(Base):
    __tablename__ = "eventos_operacionales"

    id = Column(Integer, primary_key=True, index=True)
    tipo_evento = Column(String(50))   # ARRIBO | PARTIDA | BUNCHING | ATRASO
    id_bus = Column(Integer, ForeignKey("buses.id_bus"))
    id_paradero = Column(Integer, ForeignKey("paraderos.id_paradero"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    descripcion = Column(Text)
    metadata_evento = Column(JSONB)
    id_simulacion = Column(Integer, ForeignKey("simulaciones.id_simulacion"), nullable=True)

    bus = relationship("Bus", back_populates="eventos")


class Simulacion(Base):
    __tablename__ = "simulaciones"

    id_simulacion = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200))
    estado = Column(String(20), default="PENDIENTE")  # PENDIENTE | CORRIENDO | COMPLETADO | ERROR
    parametros = Column(JSONB)
    resultado_resumen = Column(JSONB)
    fecha_inicio_sim = Column(DateTime)
    fecha_fin_sim = Column(DateTime)
    creado_en = Column(DateTime, default=datetime.utcnow)
    id_linea = Column(Integer, ForeignKey("lineas.id_linea"))


class PasajeroSimulado(Base):
    __tablename__ = "pasajeros_simulados"

    id_pasajero = Column(Integer, primary_key=True, index=True)
    id_simulacion = Column(Integer, ForeignKey("simulaciones.id_simulacion"))
    id_paradero_origen = Column(Integer, ForeignKey("paraderos.id_paradero"))
    id_paradero_destino = Column(Integer, ForeignKey("paraderos.id_paradero"))
    hora_llegada = Column(Float)    # minutos desde inicio simulación
    hora_abordaje = Column(Float)
    hora_descenso = Column(Float)
    tiempo_espera = Column(Float)
    id_bus = Column(Integer, ForeignKey("buses.id_bus"), nullable=True)


from app.models.trafico import TramoVial, EscenarioWhatIf
