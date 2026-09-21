from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class TramoVial(Base):
    __tablename__ = "tramos_viales"

    id_tramo = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, index=True)
    nombre_calle = Column(String(200), nullable=False)
    municipio = Column(String(100), nullable=False, default="Asunción", index=True)
    categoria = Column(String(50), default="ARTERIAL") # TRONCAL | ARTERIAL | COLECTORA | RESIDENCIAL
    sentido = Column(String(20), default="DOBLE") # DOBLE | UNICO_DIRECTO | UNICO_INVERSO | CERRADO
    
    # Nodos de intersección para grafo de tráfico
    nodo_origen = Column(String(50), nullable=False, index=True)
    nodo_destino = Column(String(50), nullable=False, index=True)
    
    carriles = Column(Integer, default=2)
    longitud_m = Column(Float, default=500.0)
    velocidad_limite_kmh = Column(Float, default=50.0)
    capacidad_veh_hora = Column(Integer, default=1600)
    flujo_base_veh_hora = Column(Integer, default=800)
    
    # Geometría y rutas de transporte
    geom = Column(Geometry("LINESTRING", srid=4326), nullable=True)
    coordenadas = Column(JSONB, nullable=True) # Lista de [lat, lon] para renderizado directo en GeoJSON/Leaflet
    lineas_colectivo = Column(JSONB, default=list) # e.g. ["12", "15-1", "30"]
    
    estado = Column(Boolean, default=True)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EscenarioWhatIf(Base):
    __tablename__ = "escenarios_what_if"

    id_escenario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    municipio = Column(String(100), nullable=False, default="Asunción")
    franja_horaria = Column(String(50), default="PICO_MANANA") # PICO_MANANA | PICO_TARDE | VALLE
    descripcion = Column(Text, nullable=True)
    
    # Modificaciones aplicadas al escenario (e.g. [{id_tramo: 1, nuevo_sentido: 'UNICO_INVERSO'}])
    modificaciones = Column(JSONB, nullable=False, default=list)
    
    # Resultados calculados por el motor BPR
    kpis_resultado = Column(JSONB, nullable=True)
    
    creado_por = Column(String(100), default="Departamento de Tránsito")
    creado_en = Column(DateTime, default=datetime.utcnow)
