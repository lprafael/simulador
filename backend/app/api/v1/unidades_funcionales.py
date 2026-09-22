import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.core.database import get_db, get_cid_db, get_monitoreo_db, get_billetaje_db
from app.services.cid_service import cid_service
from app.services.uf_analysis_service import uf_analysis_service
from app.schemas import LineaResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("")
def listar_unidades_funcionales(cid_db: Session = Depends(get_cid_db)):
    """Lista todas las UFs desde SisCID/Gestion_UF."""
    logger.info("📡 Petición recibida: Listar Unidades Funcionales")
    if not cid_db:
        logger.warning("⚠️ Conexión a CID no disponible")
        return []
    
    try:
        data = cid_service.get_estructura_uf(cid_db)
        logger.info(f"✅ Se obtuvieron {len(data)} UFs del CID")
        return data
    except Exception as e:
        logger.error(f"❌ Error al consultar UFs en CID: {e}")
        raise HTTPException(status_code=500, detail=f"Error en base de datos CID: {str(e)}")

@router.get("/{id_uf}/lineas", response_model=List[LineaResponse])
def listar_lineas_por_uf(id_uf: int, cid_db: Session = Depends(get_cid_db)):
    """Lista las líneas que pertenecen a una UF específica."""
    if not cid_db:
        return []
    
    lineas = cid_service.get_lineas_por_uf(cid_db, id_uf)
    
    return [
        {
            "id_linea": l["id_linea"],
            "codigo": l["numero_linea"],
            "nombre": l["nombre_comercial"] or f"Línea {l['numero_linea']}",
            "descripcion": l.get("identificador_troncal", "Servicio Regular"),
            "color_hex": l.get("color_hex", "#3B82F6"),
            "estado": True
        }
        for l in lineas
    ]
    
@router.get("/{id_uf}/historico-gps")
def get_historico_gps(id_uf: int, fecha: str, cid_db: Session = Depends(get_cid_db), monitoreo_db: Session = Depends(get_monitoreo_db)):
    """Retorna posiciones históricas para una UF y fecha."""
    if not cid_db or not monitoreo_db:
        raise HTTPException(status_code=503, detail="Servicio de base de datos no disponible")
    
    posiciones = cid_service.get_historico_gps_uf(cid_db, monitoreo_db, id_uf, fecha)
    return posiciones

@router.get("/{id_uf}/geometrias")
def get_geometrias_uf(id_uf: int, cid_db: Session = Depends(get_cid_db)):
    """Retorna las geometrías de todas las rutas de una UF."""
    if not cid_db:
        return []
    
    # Obtener rutas de la UF
    query_rutas = text("""
        SELECT DISTINCT ruta_hex 
        FROM gestion_uf.composicion_uf 
        WHERE id_uf = :id_uf
    """)
    rutas = cid_db.execute(query_rutas, {"id_uf": id_uf}).fetchall()
    
    geometrias = []
    for r in rutas:
        geom = cid_service.get_geometria_ruta(cid_db, r.ruta_hex)
        if geom:
            geometrias.append({
                "ruta_hex": r.ruta_hex,
                "geojson": geom["geojson"]
            })
    
    return geometrias

@router.get("/{id_uf}/simular-carga")
def simular_carga_uf(
    id_uf: int,
    fecha: str,
    hora_inicio: int = 0,
    hora_fin: int = 24,
    buf_troncal_m: float = 90.0,
    sep_entrada_min: int = 45,
    ventana_val_min: int = 60,
    cid_db: Session = Depends(get_cid_db),
    monitoreo_db: Session = Depends(get_monitoreo_db),
    billetaje_db: Session = Depends(get_billetaje_db),
):
    """
    Simula la carga de la UF analizando buses entrando a troncales y validaciones previas.
    Parámetros configurables:
    - hora_inicio / hora_fin: ventana horaria de análisis (0-24)
    - buf_troncal_m: buffer en metros para geocercas de troncal
    - sep_entrada_min: separación mínima entre ingresos del mismo bus a la misma zona
    - ventana_val_min: ventana de validaciones previas al ingreso
    """
    if not cid_db or not monitoreo_db:
        raise HTTPException(status_code=503, detail="Bases de datos de CID o Monitoreo no están disponibles")

    try:
        data = uf_analysis_service.get_simulation_data(
            cid_db, monitoreo_db, billetaje_db, id_uf, fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            buf_troncal_m=buf_troncal_m,
            sep_entrada_min=sep_entrada_min,
            ventana_val_min=ventana_val_min,
        )
        return data
    except Exception as e:
        logger.error(f"Error en simulación de carga UF {id_uf}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id_uf}/referencias-geograficas")
def get_referencias_geograficas_uf(id_uf: int, cid_db: Session = Depends(get_cid_db)):
    """
    Retorna troncales y geocercas de referencia para la UF seleccionada.
    """
    if not cid_db:
        raise HTTPException(status_code=503, detail="Base de datos CID no disponible")
    
    try:
        troncales = cid_service.get_uf_troncales(cid_db, id_uf)
        geocercas = cid_service.get_geocercas_uf(cid_db, id_uf)
        return {
            "troncales": troncales,
            "geocercas": geocercas
        }
    except Exception as e:
        logger.error(f"Error al obtener referencias de UF {id_uf}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
