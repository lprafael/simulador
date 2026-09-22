import logging
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_cid_db, get_monitoreo_db, get_billetaje_db
from app.services.carga_bus_service import carga_bus_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/analisis")
def analizar_carga_buses(
    fecha: Optional[str] = Query(None, description="Fecha de análisis YYYY-MM-DD (por defecto hoy)"),
    id_ruta: Optional[str] = Query(None, description="Filtro opcional por ruta_hex o ruta_dec (idrutaestacion)"),
    id_bus: Optional[str] = Query(None, description="Filtro opcional por identificador de bus (mean_id / idsam)"),
    hora_inicio: int = Query(5, ge=0, le=23, description="Hora de inicio de la ventana horaria"),
    hora_fin: int = Query(23, ge=1, le=24, description="Hora de fin de la ventana horaria"),
    umbral_turnaround_min: int = Query(25, ge=10, le=120, description="Minutos de parada en terminal para corte de trayecto"),
    cid_db: Session = Depends(get_cid_db),
    monitoreo_db: Session = Depends(get_monitoreo_db),
    billetaje_db: Session = Depends(get_billetaje_db),
):
    """
    Control Cruzado Trilateral y Cálculo de Carga de Buses por Trayecto:
    1) Catálogo de rutas de SisCID (public.catalogo_rutas)
    2) Telemetría GPS de Monitoreo (public.app_monitoreo_mensajeoperativo)
    3) Validaciones de Billetaje (public.c_transacciones)
    
    Segmenta cuándo el bus inició un trayecto y pasó a otro, calculando los pasajeros levantados
    acumulados para mostrarlos sobre el ícono del bus en el mapa.
    """
    if not fecha:
        fecha = date.today().isoformat()

    try:
        resultado = carga_bus_service.analizar_trayectos_y_carga(
            cid_db=cid_db,
            monitoreo_db=monitoreo_db,
            billetaje_db=billetaje_db,
            fecha_str=fecha,
            id_ruta=id_ruta,
            id_bus=id_bus,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            umbral_turnaround_min=umbral_turnaround_min
        )
        return resultado
    except Exception as e:
        logger.error(f"❌ Error en análisis de carga de buses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error en análisis de carga: {str(e)}")


@router.get("/rutas-catalogo")
def listar_rutas_catalogo(cid_db: Session = Depends(get_cid_db)):
    """
    Obtiene las rutas oficiales desde el catálogo de SisCID con idrutaestacion (ruta_dec),
    ruta_hex, sentido (ida/vuelta), origen, destino e identificación comercial.
    """
    try:
        rutas = carga_bus_service.get_catalogo_rutas(cid_db)
        return rutas
    except Exception as e:
        logger.error(f"❌ Error al consultar catálogo de rutas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buses-activos")
def listar_buses_activos(
    monitoreo_db: Session = Depends(get_monitoreo_db)
):
    """
    Retorna la lista de buses con pings GPS recientes en Monitoreo para facilitar el filtrado.
    """
    if not monitoreo_db:
        return []

    try:
        query = text("""
            SELECT DISTINCT mean_id as id_bus, route_id as ruta_hex, agency_id
            FROM public.app_monitoreo_mensajeoperativo
            WHERE fecha_hora >= CURRENT_TIMESTAMP - INTERVAL '3 hours'
              AND mean_id IS NOT NULL AND TRIM(mean_id) <> ''
            ORDER BY mean_id ASC
            LIMIT 100
        """)
        result = monitoreo_db.execute(query).fetchall()
        return [dict(r._asdict()) for r in result]
    except Exception as e:
        logger.warning(f"Error consultando buses recientes en Monitoreo: {e}")
        try:
            monitoreo_db.rollback()
        except Exception:
            pass
        return []
