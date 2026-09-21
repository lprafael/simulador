from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from app.core.database import get_cid_db, get_db, get_billetaje_db
from app.services.planning_service import planning_service
from app.services.billetaje_service import billetaje_service

router = APIRouter()

@router.get("/optimizar-flota/{id_linea}")
def optimizar_flota(
    id_linea: int, 
    frecuencia: float = 10.0,
    cid_db: Session = Depends(get_cid_db)
):
    """
    Calcula la flota optimizada para una línea según la frecuencia deseada.
    """
    if not cid_db:
        raise HTTPException(status_code=400, detail="Conexión a CID no disponible")
    
    resultado = planning_service.calcular_optimizacion_flota(cid_db, id_linea, frecuencia)
    if not resultado:
        raise HTTPException(status_code=500, detail="Error al realizar el cálculo")
    
    return resultado

@router.get("/matriz-od")
@router.get("/matriz-od/", include_in_schema=False)
def get_matriz_od(
    fecha: Optional[date] = None,
    umbral_min: int = 60,
    billetaje_db: Session = Depends(get_billetaje_db)
):
    """
    Retorna la matriz Origen-Destino estimada para una fecha.
    """
    if not fecha:
        fecha = date.today()
        
    return billetaje_service.generar_matriz_od_avanzada(billetaje_db, fecha, umbral_min)
