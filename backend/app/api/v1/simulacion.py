"""
Endpoints para gestión y ejecución de simulaciones.
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models import Simulacion, Linea, Ruta, Paradero, Bus
from app.schemas import SimulacionCreate, SimulacionResponse
from app.simulacion.motor import (
    MotorSimulacion, ConfigSimulacion, ConfigRuta, ConfigParadero
)
from app.websocket.manager import manager, posiciones_en_tiempo_real

logger = logging.getLogger(__name__)
router = APIRouter()


def _construir_config_desde_db(
    sim_data: SimulacionCreate,
    db: Session
) -> ConfigSimulacion:
    """Construye la configuración de simulación desde los datos de BD."""
    params = sim_data.parametros
    
    # Obtener línea
    linea = db.query(Linea).filter(Linea.id_linea == params.id_linea).first()
    if not linea:
        raise HTTPException(status_code=404, detail="Línea no encontrada en la base de datos local. Espere a que termine la sincronización.")
    
    # Obtener primera ruta de la línea
    ruta = db.query(Ruta).filter(Ruta.id_linea == params.id_linea).first()
    
    if ruta:
        paraderos_db = (
            db.query(Paradero)
            .filter(Paradero.id_ruta == ruta.id_ruta)
            .filter(Paradero.estado == True)
            .order_by(Paradero.orden_ruta)
            .all()
        )
        paraderos = [
            ConfigParadero(
                id_paradero=p.id_paradero,
                nombre=p.nombre or f"Paradero {p.orden_ruta}",
                orden=p.orden_ruta or i,
                distancia_m=p.distancia_desde_inicio_m or (i * 800),
                tasa_llegada_pax=params.tasa_pasajeros_por_min / max(len(paraderos_db), 1),
            )
            for i, p in enumerate(paraderos_db)
        ]
        
        config_ruta = ConfigRuta(
            id_ruta=ruta.id_ruta,
            id_linea=params.id_linea,
            nombre=ruta.nombre or linea.nombre_comercial or linea.numero_linea,
            paraderos=paraderos,
            distancia_total_km=ruta.distancia_km or 15.0,
        )
    else:
        # Ruta de prueba si no hay datos reales
        paraderos_default = [
            ConfigParadero(id_paradero=1, nombre="Terminal Norte", orden=0, distancia_m=0, tipo="INICIO", tasa_llegada_pax=0.5),
            ConfigParadero(id_paradero=2, nombre="Plaza Central", orden=1, distancia_m=2500, tasa_llegada_pax=1.5),
            ConfigParadero(id_paradero=3, nombre="Mercado", orden=2, distancia_m=5000, tasa_llegada_pax=2.0),
            ConfigParadero(id_paradero=4, nombre="Hospital", orden=3, distancia_m=7500, tasa_llegada_pax=1.0),
            ConfigParadero(id_paradero=5, nombre="Universidad", orden=4, distancia_m=10000, tasa_llegada_pax=1.8),
            ConfigParadero(id_paradero=6, nombre="Terminal Sur", orden=5, distancia_m=12000, tasa_llegada_pax=0.3),
        ]
        config_ruta = ConfigRuta(
            id_ruta=0,
            id_linea=params.id_linea,
            nombre=linea.nombre_comercial or linea.numero_linea,
            paraderos=paraderos_default,
            distancia_total_km=12.0,
        )
    
    return ConfigSimulacion(
        id_linea=params.id_linea,
        nombre_linea=linea.nombre_comercial or linea.numero_linea,
        ruta=config_ruta,
        num_buses=params.num_buses,
        headway_programado_min=params.headway_min,
        velocidad_kmh=params.velocidad_kmh,
        duracion_sim_min=params.duracion_sim_min,
        tasa_pasajeros_global=params.tasa_pasajeros_por_min,
        tiempo_parada_base_min=params.tiempo_parada_base_min,
        semilla=params.semilla_aleatoria,
    )


async def _ejecutar_simulacion_bg(id_simulacion: int, config: ConfigSimulacion):
    """Tarea de fondo para ejecutar la simulación y transmitir resultados."""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Actualizar estado a CORRIENDO
        sim = db.query(Simulacion).filter(Simulacion.id_simulacion == id_simulacion).first()
        if sim:
            sim.estado = "CORRIENDO"
            sim.fecha_inicio_sim = datetime.utcnow()
            db.commit()
        
        # Broadcast inicio
        await manager.broadcast({
            "tipo": "SIMULACION_INICIO",
            "id_simulacion": id_simulacion,
            "nombre": config.nombre_linea,
        }, room=f"sim_{id_simulacion}")
        
        # Ejecutar motor (en hilo separado para no bloquear event loop)
        motor = MotorSimulacion(config)
        resultado = await asyncio.to_thread(motor.ejecutar, id_simulacion)
        
        # Guardar resultado en BD
        sim = db.query(Simulacion).filter(Simulacion.id_simulacion == id_simulacion).first()
        if sim:
            sim.estado = "COMPLETADO"
            sim.fecha_fin_sim = datetime.utcnow()
            sim.resultado_resumen = {
                "headway_promedio_min": resultado.headway_promedio_min,
                "headway_std_min": resultado.headway_std_min,
                "regularidad_pct": resultado.regularidad_pct,
                "pct_bunching": resultado.pct_bunching,
                "velocidad_comercial_kmh": resultado.velocidad_comercial_kmh,
                "total_pasajeros": resultado.total_pasajeros_transportados,
                "total_eventos": resultado.total_eventos,
                "estados_buses": resultado.estados_buses,
                "posiciones": resultado.posiciones,
                "eventos": resultado.eventos[:100],
                "headways": {
                    str(k): v for k, v in resultado.headways_por_paradero.items()
                }
            }
            db.commit()
        
        # Transmitir resultado completo por WS
        await manager.broadcast({
            "tipo": "SIMULACION_COMPLETADA",
            "id_simulacion": id_simulacion,
            "resultado": {
                "headway_promedio_min": resultado.headway_promedio_min,
                "regularidad_pct": resultado.regularidad_pct,
                "pct_bunching": resultado.pct_bunching,
                "total_pasajeros": resultado.total_pasajeros_transportados,
                "total_eventos": resultado.total_eventos,
                "posiciones": resultado.posiciones[:200],
                "eventos": resultado.eventos[:100],
            }
        }, room=f"sim_{id_simulacion}")
        
        # También broadcast a sala general
        await manager.broadcast_all({
            "tipo": "SIMULACION_COMPLETADA",
            "id_simulacion": id_simulacion,
            "resumen": {
                "headway_promedio_min": resultado.headway_promedio_min,
                "regularidad_pct": resultado.regularidad_pct,
                "pct_bunching": resultado.pct_bunching,
            }
        })
        
        logger.info(f"✅ Simulación {id_simulacion} completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error en simulación {id_simulacion}: {e}")
        sim = db.query(Simulacion).filter(Simulacion.id_simulacion == id_simulacion).first()
        if sim:
            sim.estado = "ERROR"
            db.commit()
        
        await manager.broadcast({
            "tipo": "SIMULACION_ERROR",
            "id_simulacion": id_simulacion,
            "error": str(e),
        }, room=f"sim_{id_simulacion}")
    finally:
        db.close()


@router.get("", response_model=List[SimulacionResponse])
def listar_simulaciones(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lista todas las simulaciones."""
    return (
        db.query(Simulacion)
        .order_by(Simulacion.creado_en.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{id_simulacion}", response_model=SimulacionResponse)
def obtener_simulacion(id_simulacion: int, db: Session = Depends(get_db)):
    """Obtiene detalles de una simulación."""
    sim = db.query(Simulacion).filter(Simulacion.id_simulacion == id_simulacion).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulación no encontrada")
    return sim


@router.post("", response_model=SimulacionResponse, status_code=201)
async def crear_y_ejecutar_simulacion(
    sim_data: SimulacionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Crea una nueva simulación y la ejecuta en background."""
    logger.info(f"🚀 Solicitud de nueva simulación recibida para línea ID: {sim_data.parametros.id_linea}")
    
    # Construir config (valida existencia de línea, etc.)
    config = _construir_config_desde_db(sim_data, db)
    
    # Guardar en BD
    sim = Simulacion(
        nombre=sim_data.nombre,
        estado="PENDIENTE",
        parametros=sim_data.parametros.model_dump(),
        id_linea=sim_data.parametros.id_linea,
    )
    db.add(sim)
    db.commit()
    db.refresh(sim)
    
    # Ejecutar en background
    background_tasks.add_task(
        _ejecutar_simulacion_bg,
        sim.id_simulacion,
        config
    )
    
    return sim


@router.post("/demo", response_model=dict)
async def ejecutar_simulacion_demo(background_tasks: BackgroundTasks):
    """
    Ejecuta una simulación de DEMO sin necesidad de base de datos.
    Útil para probar el sistema sin datos reales.
    """
    from app.simulacion.motor import ConfigParadero
    
    paraderos_demo = [
        ConfigParadero(id_paradero=1, nombre="Terminal Norte", orden=0, distancia_m=0, tasa_llegada_pax=0.5),
        ConfigParadero(id_paradero=2, nombre="Avda. Eusebio Ayala", orden=1, distancia_m=1800, tasa_llegada_pax=2.0),
        ConfigParadero(id_paradero=3, nombre="Mercado 4", orden=2, distancia_m=4200, tasa_llegada_pax=3.0),
        ConfigParadero(id_paradero=4, nombre="Plaza de los Héroes", orden=3, distancia_m=6500, tasa_llegada_pax=2.5),
        ConfigParadero(id_paradero=5, nombre="Hospital de Clínicas", orden=4, distancia_m=8800, tasa_llegada_pax=1.5),
        ConfigParadero(id_paradero=6, nombre="UNA - FCQ", orden=5, distancia_m=11000, tasa_llegada_pax=2.0),
        ConfigParadero(id_paradero=7, nombre="Shopping del Sol", orden=6, distancia_m=13500, tasa_llegada_pax=1.8),
        ConfigParadero(id_paradero=8, nombre="Terminal Sur", orden=7, distancia_m=15000, tasa_llegada_pax=0.3),
    ]
    
    config_demo = ConfigSimulacion(
        id_linea=1,
        nombre_linea="Línea 30 - Demo Asunción",
        ruta=ConfigRuta(
            id_ruta=1,
            id_linea=1,
            nombre="Terminal Norte - Terminal Sur (IDA)",
            paraderos=paraderos_demo,
            distancia_total_km=15.0,
        ),
        num_buses=6,
        headway_programado_min=8.0,
        velocidad_kmh=22.0,
        duracion_sim_min=90.0,
        tasa_pasajeros_global=15.0,
        semilla=42,
    )
    
    # Ejecutar en hilo separado para no bloquear event loop
    motor = MotorSimulacion(config_demo)
    resultado = await asyncio.to_thread(motor.ejecutar, id_simulacion=0)
    
    return {
        "id_simulacion": 0,
        "estado": "COMPLETADO",
        "nombre": resultado.nombre,
        "duracion_sim_min": resultado.duracion_sim_min,
        "kpis": {
            "headway_promedio_min": resultado.headway_promedio_min,
            "headway_std_min": resultado.headway_std_min,
            "regularidad_pct": resultado.regularidad_pct,
            "pct_bunching": resultado.pct_bunching,
            "velocidad_comercial_kmh": resultado.velocidad_comercial_kmh,
            "total_pasajeros": resultado.total_pasajeros_transportados,
            "total_eventos": resultado.total_eventos,
        },
        "posiciones": resultado.posiciones,
        "eventos": resultado.eventos,
        "estados_buses": resultado.estados_buses,
        "headways": {
            str(k): v for k, v in resultado.headways_por_paradero.items()
        }
    }
