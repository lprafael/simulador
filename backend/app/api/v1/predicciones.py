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
        bus_interno = f"{id_bus:03d}"
    else:
        bus_interno = bus.interno or f"{id_bus:03d}"
        
    from app.websocket.manager import posiciones_en_tiempo_real
    pos_actual = posiciones_en_tiempo_real.get(id_bus)
    
    if not pos_actual:
        # Posición simulada coherente según ID de bus para variedad visual
        pos_m = float((id_bus * 1250) % 7000)
        v_kmh = 20.0 + float((id_bus * 3) % 12)
    else:
        # En una implementación real, mapearíamos lat/lon a posición_m en la ruta
        pos_m = float(pos_actual.get("posicion_m", 500.0))
        v_kmh = float(pos_actual.get("velocidad", 22.0))

    # Obtener paraderos de la ruta activa del bus
    paraderos_db = (
        db.query(Paradero)
        .order_by(Paradero.orden_ruta)
        .all()
    )
    
    if not paraderos_db:
        paraderos = [
            {"id_paradero": 1, "nombre": "Terminal Fernando de la Mora", "distancia_m": 0.0, "tipo": "INICIO"},
            {"id_paradero": 2, "nombre": "Avda. Mcal. López y Madame Lynch", "distancia_m": 2200.0, "tipo": "INTERMEDIO"},
            {"id_paradero": 3, "nombre": "Cruce Avda. Eusebio Ayala", "distancia_m": 4100.0, "tipo": "INTERMEDIO"},
            {"id_paradero": 4, "nombre": "Mercado 4", "distancia_m": 6800.0, "tipo": "INTERMEDIO"},
            {"id_paradero": 5, "nombre": "Plaza de los Héroes / Microcentro", "distancia_m": 8900.0, "tipo": "INTERMEDIO"},
            {"id_paradero": 6, "nombre": "Terminal Ómnibus Asunción", "distancia_m": 11500.0, "tipo": "TERMINAL"},
        ]
    else:
        paraderos = [
            {
                "id_paradero": p.id_paradero,
                "nombre": p.nombre,
                "distancia_m": float(p.distancia_desde_inicio_m or (i * 1800.0)),
                "tipo": p.tipo or "INTERMEDIO"
            }
            for i, p in enumerate(paraderos_db)
        ]
    
    etas = prediction_service.calcular_eta_proyectado(
        posicion_actual_m=pos_m,
        velocidad_actual_kmh=v_kmh,
        paraderos_restantes=paraderos
    )
    
    if not etas and paraderos:
        etas = prediction_service.calcular_eta_proyectado(
            posicion_actual_m=0.0,
            velocidad_actual_kmh=v_kmh,
            paraderos_restantes=paraderos[1:]
        )
    
    return {
        "id_bus": id_bus,
        "interno": bus_interno,
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
