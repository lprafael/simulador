from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import Bus, Empresa
from app.schemas import BusCreate, BusResponse

router = APIRouter()


@router.get("", response_model=List[BusResponse])
def listar_buses(
    skip: int = 0,
    limit: int = 100,
    estado: str = None,
    db: Session = Depends(get_db)
):
    """Lista todos los buses con filtros opcionales."""
    query = db.query(Bus)
    if estado:
        query = query.filter(Bus.estado == estado)
    return query.offset(skip).limit(limit).all()


@router.get("/{id_bus}", response_model=BusResponse)
def obtener_bus(id_bus: int, db: Session = Depends(get_db)):
    """Obtiene un bus por ID."""
    bus = db.query(Bus).filter(Bus.id_bus == id_bus).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus no encontrado")
    return bus


@router.post("", response_model=BusResponse, status_code=201)
def crear_bus(bus_data: BusCreate, db: Session = Depends(get_db)):
    """Crea un nuevo bus."""
    bus = Bus(**bus_data.model_dump())
    db.add(bus)
    db.commit()
    db.refresh(bus)
    return bus


@router.put("/{id_bus}", response_model=BusResponse)
def actualizar_bus(id_bus: int, bus_data: BusCreate, db: Session = Depends(get_db)):
    """Actualiza un bus existente."""
    bus = db.query(Bus).filter(Bus.id_bus == id_bus).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus no encontrado")
    
    for key, value in bus_data.model_dump(exclude_unset=True).items():
        setattr(bus, key, value)
    
    db.commit()
    db.refresh(bus)
    return bus


@router.delete("/{id_bus}")
def eliminar_bus(id_bus: int, db: Session = Depends(get_db)):
    """Elimina (desactiva) un bus."""
    bus = db.query(Bus).filter(Bus.id_bus == id_bus).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus no encontrado")
    bus.estado = "INACTIVO"
    db.commit()
    return {"mensaje": "Bus desactivado", "id_bus": id_bus}


@router.get("/empresa/{id_empresa}", response_model=List[BusResponse])
def buses_por_empresa(id_empresa: int, db: Session = Depends(get_db)):
    """Lista buses de una empresa específica."""
    return db.query(Bus).filter(Bus.id_empresa == id_empresa).all()
