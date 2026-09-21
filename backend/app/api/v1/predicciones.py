from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
from app.core.database import get_db
from app.models import Bus, Ruta, Paradero
from app.services.prediction_service import prediction_service

router = APIRouter()

@router.get("/eta/{id_bus}")
def obtener_prediccion_eta(id_bus: int, db: Session = Depends(get_db)):
    """
    Retorna los tiempos estimados de llegada a los siguientes paraderos
    para un bus específico basándose en su última posición conocida.
    """
    # Obtener bus y su última posición
    bus = db.query(Bus).filter(Bus.id_bus == id_bus).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus no encontrado")
        
    from app.websocket.manager import posiciones_en_tiempo_real
    pos_actual = posiciones_en_tiempo_real.get(id_bus)
    
    if not pos_actual:
        # Si no está en memoria, buscar en BD (demo: usar paradero inicio si no hay GPS)
        pos_m = 0.0
        v_kmh = 25.0
    else:
        # En una implementación real, mapearíamos lat/lon a posición_m en la ruta
        # Para la demo, usaremos un valor derivado o simulado
        pos_m = pos_actual.get("posicion_m", 500.0)
        v_kmh = pos_actual.get("velocidad", 22.0)

    # Obtener paraderos de la ruta activa del bus (demo: línea 1)
    paraderos_db = (
        db.query(Paradero)
        .order_by(Paradero.orden_ruta)
        .all()
    )
    
    paraderos = [
        {
            "id_paradero": p.id_paradero,
            "nombre": p.nombre,
            "distancia_m": float(p.distancia_desde_inicio_m or 0),
            "tipo": p.tipo
        }
        for p in paraderos_db
    ]
    
    etas = prediction_service.calcular_eta_proyectado(
        posicion_actual_m=pos_m,
        velocidad_actual_kmh=v_kmh,
        paraderos_restantes=paraderos
    )
    
    return {
        "id_bus": id_bus,
        "interno": bus.interno,
        "posicion_actual_m": pos_m,
        "velocidad_actual_kmh": v_kmh,
        "predicciones": etas
    }

@router.get("/optimizacion/{id_linea}")
def sugerir_optimizacion(id_linea: int, demanda: float = 500.0):
    """
    Sugiere mejoras en la frecuencia basándose en la demanda proyectada.
    """
    # Demo: tiempo de ciclo base de 60 min
    res = prediction_service.optimizar_frecuencia(
        demanda_pax_hora=demanda,
        capacidad_bus=45,
        tiempo_ciclo_min=60.0
    )
    return {
        "id_linea": id_linea,
        "analisis": res,
        "recomendacion": f"Se recomienda un despacho cada {res['headway_sugerido_min']} minutos."
    }
