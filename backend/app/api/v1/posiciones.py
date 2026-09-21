from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.models import PosicionGPS, Bus
from app.schemas import PosicionGPSCreate, PosicionGPSResponse
from app.websocket.manager import manager, posiciones_en_tiempo_real

router = APIRouter()


@router.get("/tiempo-real", response_model=List[dict])
async def posiciones_actuales():
    """Retorna las últimas posiciones conocidas de todos los buses (en memoria)."""
    return list(posiciones_en_tiempo_real.values())


@router.get("/bus/{id_bus}", response_model=List[PosicionGPSResponse])
def posiciones_por_bus(
    id_bus: int,
    limite: int = 100,
    db: Session = Depends(get_db)
):
    """Retorna las últimas posiciones de un bus."""
    return (
        db.query(PosicionGPS)
        .filter(PosicionGPS.id_bus == id_bus)
        .order_by(desc(PosicionGPS.timestamp))
        .limit(limite)
        .all()
    )


@router.post("/", response_model=PosicionGPSResponse, status_code=201)
async def registrar_posicion(
    pos_data: PosicionGPSCreate,
    db: Session = Depends(get_db)
):
    """Registra una nueva posición GPS y la transmite por WebSocket."""
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point
    
    posicion = PosicionGPS(
        id_bus=pos_data.id_bus,
        lat=pos_data.lat,
        lon=pos_data.lon,
        velocidad=pos_data.velocidad,
        rumbo=pos_data.rumbo,
        fuente=pos_data.fuente,
        geom=from_shape(Point(pos_data.lon, pos_data.lat), srid=4326),
        timestamp=datetime.utcnow(),
    )
    
    db.add(posicion)
    db.commit()
    db.refresh(posicion)
    
    # Actualizar estado en memoria y broadcast
    pos_dict = {
        "id": posicion.id,
        "id_bus": pos_data.id_bus,
        "lat": pos_data.lat,
        "lon": pos_data.lon,
        "velocidad": pos_data.velocidad,
        "rumbo": pos_data.rumbo,
        "timestamp": datetime.utcnow().isoformat(),
    }
    posiciones_en_tiempo_real[pos_data.id_bus] = pos_dict
    
    await manager.broadcast({
        "tipo": "POSICION_GPS",
        "datos": pos_dict,
    }, room="posiciones")
    
    return posicion


@router.get("/historico/{id_bus}")
def historico_posiciones(
    id_bus: int,
    desde: datetime = None,
    hasta: datetime = None,
    db: Session = Depends(get_db)
):
    """Retorna el historial de posiciones para reproducción."""
    query = db.query(PosicionGPS).filter(PosicionGPS.id_bus == id_bus)
    
    if desde:
        query = query.filter(PosicionGPS.timestamp >= desde)
    if hasta:
        query = query.filter(PosicionGPS.timestamp <= hasta)
    
    posiciones = query.order_by(PosicionGPS.timestamp).limit(1000).all()
    
    return [
        {
            "lat": p.lat,
            "lon": p.lon,
            "velocidad": p.velocidad,
            "timestamp": p.timestamp.isoformat() if p.timestamp else None,
        }
        for p in posiciones
    ]
