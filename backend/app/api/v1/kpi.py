"""
Endpoints para KPIs operacionales del sistema.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models import PosicionGPS, Bus, Linea, EventoOperacional, Simulacion

router = APIRouter()


@router.get("/resumen")
def kpi_resumen_general(db: Session = Depends(get_db)):
    """KPI resumen general del sistema."""
    total_buses = db.query(Bus).filter(Bus.estado == "ACTIVO").count()
    total_lineas = db.query(Linea).filter(Linea.estado == True).count()
    total_simulaciones = db.query(Simulacion).count()
    
    # Última simulación completada
    ultima_sim = (
        db.query(Simulacion)
        .filter(Simulacion.estado == "COMPLETADO")
        .order_by(desc(Simulacion.creado_en))
        .first()
    )
    
    kpis_ultima_sim = {}
    if ultima_sim and ultima_sim.resultado_resumen:
        kpis_ultima_sim = ultima_sim.resultado_resumen
    
    return {
        "total_buses_activos": total_buses,
        "total_lineas_activas": total_lineas,
        "total_simulaciones": total_simulaciones,
        "ultima_simulacion": {
            "id": ultima_sim.id_simulacion if ultima_sim else None,
            "nombre": ultima_sim.nombre if ultima_sim else None,
            "kpis": kpis_ultima_sim,
        }
    }


@router.get("/simulacion/{id_simulacion}")
def kpi_simulacion(id_simulacion: int, db: Session = Depends(get_db)):
    """KPIs de una simulación específica."""
    sim = db.query(Simulacion).filter(Simulacion.id_simulacion == id_simulacion).first()
    if not sim:
        return {"error": "Simulación no encontrada"}
    
    return {
        "id_simulacion": id_simulacion,
        "nombre": sim.nombre,
        "estado": sim.estado,
        "parametros": sim.parametros,
        "resultado": sim.resultado_resumen,
        "fecha_creacion": sim.creado_en.isoformat() if sim.creado_en else None,
        "fecha_inicio": sim.fecha_inicio_sim.isoformat() if sim.fecha_inicio_sim else None,
        "fecha_fin": sim.fecha_fin_sim.isoformat() if sim.fecha_fin_sim else None,
    }


@router.get("/eventos/recientes")
def eventos_recientes(
    limite: int = 50,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista los eventos operacionales más recientes."""
    query = db.query(EventoOperacional)
    if tipo:
        query = query.filter(EventoOperacional.tipo_evento == tipo)
    
    eventos = (
        query
        .order_by(desc(EventoOperacional.timestamp))
        .limit(limite)
        .all()
    )
    
    return [
        {
            "id": e.id,
            "tipo": e.tipo_evento,
            "id_bus": e.id_bus,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "descripcion": e.descripcion,
        }
        for e in eventos
    ]


@router.get("/headway/{id_linea}")
def kpi_headway(id_linea: int, db: Session = Depends(get_db)):
    """KPI de headway para una línea."""
    # Buscar en última simulación de la línea
    ultima_sim = (
        db.query(Simulacion)
        .filter(Simulacion.id_linea == id_linea)
        .filter(Simulacion.estado == "COMPLETADO")
        .order_by(desc(Simulacion.creado_en))
        .first()
    )
    
    if ultima_sim and ultima_sim.resultado_resumen:
        res = ultima_sim.resultado_resumen
        return {
            "id_linea": id_linea,
            "fuente": "ultima_simulacion",
            "headway_promedio_min": res.get("headway_promedio_min", 0),
            "headway_std_min": res.get("headway_std_min", 0),
            "regularidad_pct": res.get("regularidad_pct", 0),
            "pct_bunching": res.get("pct_bunching", 0),
        }
    
    return {
        "id_linea": id_linea,
        "fuente": "sin_datos",
        "mensaje": "No hay simulaciones completadas para esta línea",
    }


@router.get("/congestion")
@router.get("/congestion/", include_in_schema=False)
def get_congestion_actual():
    """
    Retorna el estado de congestión calculado internamente
    comparando velocidad real de buses vs comercial.
    """
    from app.websocket.manager import posiciones_en_tiempo_real
    from app.services.congestion_service import congestion_service
    
    # Tomar las posiciones actuales de los buses en memoria
    posiciones = list(posiciones_en_tiempo_real.values())
    return congestion_service.calcular_congestion_interna(posiciones)


@router.get("/incidentes-waze")
@router.get("/incidentes-waze/", include_in_schema=False)
async def get_incidentes_waze():
    """
    Retorna alertas e incidentes desde el feed de Waze for Cities.
    """
    from app.services.congestion_service import congestion_service
    return await congestion_service.get_waze_alerts()
