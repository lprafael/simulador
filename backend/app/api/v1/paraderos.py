from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import Paradero
from app.schemas import ParaderoCreate, ParaderoResponse

router = APIRouter()


@router.get("/", response_model=List[ParaderoResponse])
def listar_paraderos(
    id_ruta: int = None,
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    query = db.query(Paradero).filter(Paradero.estado == True)
    if id_ruta:
        query = query.filter(Paradero.id_ruta == id_ruta)
    return query.order_by(Paradero.orden_ruta).offset(skip).limit(limit).all()


@router.get("/{id_paradero}", response_model=ParaderoResponse)
def obtener_paradero(id_paradero: int, db: Session = Depends(get_db)):
    paradero = db.query(Paradero).filter(Paradero.id_paradero == id_paradero).first()
    if not paradero:
        raise HTTPException(status_code=404, detail="Paradero no encontrado")
    return paradero


@router.post("/", response_model=ParaderoResponse, status_code=201)
def crear_paradero(paradero_data: ParaderoCreate, db: Session = Depends(get_db)):
    data = paradero_data.model_dump()
    lat = data.pop("lat", None)
    lon = data.pop("lon", None)
    
    paradero = Paradero(**data)
    
    if lat and lon:
        from geoalchemy2.shape import from_shape
        from shapely.geometry import Point
        paradero.geom = from_shape(Point(lon, lat), srid=4326)
    
    db.add(paradero)
    db.commit()
    db.refresh(paradero)
    return paradero
