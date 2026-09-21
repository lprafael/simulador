from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from app.core.database import get_db, get_cid_db
from app.models import Linea, Empresa
from app.schemas import LineaCreate, LineaResponse
from app.services.cid_service import cid_service

router = APIRouter()


@router.get("", response_model=List[LineaResponse])
def listar_lineas(db: Session = Depends(get_db)):
    """Lista las líneas que ya han sido sincronizadas localmente."""
    lineas_locales = db.query(Linea).filter(Linea.estado == True).all()
    return [
        {
            "id_linea": l.id_linea,
            "codigo": l.numero_linea,
            "nombre": l.nombre_comercial or f"Línea {l.numero_linea}",
            "descripcion": l.identificador_troncal or "Servicio Regular",
            "color_hex": l.color_hex or "#3B82F6",
            "estado": l.estado
        }
        for l in lineas_locales
    ]


@router.get("/{id_linea}/rutas")
def listar_rutas_por_linea(
    id_linea: int,
    cid_db: Session = Depends(get_cid_db)
):
    """Obtiene las rutas técnicas vinculadas a una línea."""
    if not cid_db:
        return []
    return cid_service.get_rutas_por_linea(cid_db, id_linea)


@router.get("/{id_linea}", response_model=LineaResponse)
def obtener_linea(id_linea: int, db: Session = Depends(get_db)):
    linea = db.query(Linea).filter(Linea.id_linea == id_linea).first()
    if not linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    return linea


@router.post("/", response_model=LineaResponse, status_code=201)
def crear_linea(linea_data: LineaCreate, db: Session = Depends(get_db)):
    linea = Linea(**linea_data.model_dump())
    db.add(linea)
    db.commit()
    db.refresh(linea)
    return linea


@router.put("/{id_linea}", response_model=LineaResponse)
def actualizar_linea(id_linea: int, linea_data: LineaCreate, db: Session = Depends(get_db)):
    linea = db.query(Linea).filter(Linea.id_linea == id_linea).first()
    if not linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    for key, value in linea_data.model_dump(exclude_unset=True).items():
        setattr(linea, key, value)
    db.commit()
    db.refresh(linea)
    return linea


@router.delete("/{id_linea}")
def eliminar_linea(id_linea: int, db: Session = Depends(get_db)):
    linea = db.query(Linea).filter(Linea.id_linea == id_linea).first()
    if not linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    linea.estado = False
    db.commit()
    return {"mensaje": "Línea desactivada", "id_linea": id_linea}

@router.get("/geometria/{ruta_hex}")
def obtener_geometria_real(
    ruta_hex: str,
    cid_db: Session = Depends(get_cid_db)
):
    """Retorna el GeoJSON de la ruta directamente desde SisCID usando ruta_hex."""
    if not cid_db:
        raise HTTPException(status_code=400, detail="Conexión a SisCID no configurada")
    
    geometria = cid_service.get_geometria_ruta(cid_db, ruta_hex)
    if not geometria:
        raise HTTPException(status_code=404, detail="Geometría no encontrada para esta ruta")
    
    return json.loads(geometria["geojson"])
