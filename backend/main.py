from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
import os

import redis as redis_sync

from app.core.config import settings
from app.core.database import engine, Base, get_monitoreo_db
from app.api.v1 import router as api_router
from app.websocket.manager import ws_router
from app.services.avl_service import AvlInboundService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client síncrono solo para el lock del worker AVL
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
_redis_client = redis_sync.from_url(REDIS_URL, decode_responses=True)
AVL_LOCK_KEY = "avl:streaming:lock"
AVL_LOCK_TTL = 30  # segundos; el worker renueva el lock cada ciclo de polling

# Inicializar servicio AVL
avl_service = AvlInboundService(get_monitoreo_db)


def _ensure_seed_data():
    try:
        from app.core.database import SessionLocal
        from app.models import Bus, Empresa, Paradero
        with SessionLocal() as db:
            if db.query(Bus).count() == 0:
                logger.info("🌱 Inicializando flota base de buses y paraderos...")
                emp1 = Empresa(id_empresa=1, nombre="Empresa de Transporte Automotor San Isidro S.R.L.", codigo_eot="EOT-001", ruc="80012345-1", estado=True)
                emp2 = Empresa(id_empresa=2, nombre="Transportistas Unidos S.A.", codigo_eot="EOT-002", ruc="80054321-2", estado=True)
                db.merge(emp1)
                db.merge(emp2)
                db.commit()

                buses_seed = [
                    Bus(id_bus=1, interno="001", placa="ABC-001", capacidad=45, estado="ACTIVO", modelo="Agrale MA 15.0", anio=2019, id_empresa=1),
                    Bus(id_bus=2, interno="002", placa="ABC-002", capacidad=45, estado="ACTIVO", modelo="Agrale MA 15.0", anio=2019, id_empresa=1),
                    Bus(id_bus=3, interno="003", placa="ABC-003", capacidad=45, estado="ACTIVO", modelo="Agrale MA 15.0", anio=2020, id_empresa=1),
                    Bus(id_bus=4, interno="004", placa="ABC-004", capacidad=45, estado="ACTIVO", modelo="Marcopolo Torino", anio=2021, id_empresa=1),
                    Bus(id_bus=5, interno="005", placa="ABC-005", capacidad=45, estado="ACTIVO", modelo="Marcopolo Torino", anio=2021, id_empresa=1),
                    Bus(id_bus=6, interno="006", placa="ABC-006", capacidad=45, estado="ACTIVO", modelo="Marcopolo Torino", anio=2022, id_empresa=1),
                    Bus(id_bus=7, interno="007", placa="DEF-001", capacidad=45, estado="ACTIVO", modelo="Mercedes OF-1721", anio=2020, id_empresa=2),
                    Bus(id_bus=8, interno="008", placa="DEF-002", capacidad=45, estado="ACTIVO", modelo="Mercedes OF-1721", anio=2020, id_empresa=2),
                    Bus(id_bus=9, interno="009", placa="DEF-003", capacidad=45, estado="ACTIVO", modelo="Mercedes OF-1721", anio=2021, id_empresa=2),
                    Bus(id_bus=10, interno="010", placa="DEF-004", capacidad=45, estado="ACTIVO", modelo="Caio Apache Vip", anio=2022, id_empresa=2),
                    Bus(id_bus=11, interno="011", placa="GHI-001", capacidad=50, estado="ACTIVO", modelo="Caio Apache Vip", anio=2022, id_empresa=2),
                    Bus(id_bus=12, interno="012", placa="GHI-002", capacidad=50, estado="ACTIVO", modelo="Caio Apache Vip", anio=2023, id_empresa=2),
                    Bus(id_bus=13, interno="013", placa="GHI-003", capacidad=50, estado="ACTIVO", modelo="Caio Apache Vip", anio=2023, id_empresa=2),
                    Bus(id_bus=14, interno="014", placa="GHI-004", capacidad=45, estado="INACTIVO", modelo="Agrale MA 15.0", anio=2018, id_empresa=1),
                    Bus(id_bus=15, interno="015", placa="GHI-005", capacidad=45, estado="MANTENIMIENTO", modelo="Agrale MA 15.0", anio=2018, id_empresa=1),
                ]
                for b in buses_seed:
                    db.merge(b)

                if db.query(Paradero).count() == 0:
                    paraderos_seed = [
                        Paradero(id_paradero=1, nombre="Terminal Fernando de la Mora", tipo="INICIO", lat=-25.3390, lon=-57.5200, orden_ruta=1, distancia_desde_inicio_m=0, estado=True),
                        Paradero(id_paradero=2, nombre="Avda. Mcal. López y Madame Lynch", tipo="INTERMEDIO", lat=-25.3350, lon=-57.5100, orden_ruta=2, distancia_desde_inicio_m=2200, estado=True),
                        Paradero(id_paradero=3, nombre="Cruce Avda. Eusebio Ayala", tipo="INTERMEDIO", lat=-25.3300, lon=-57.5000, orden_ruta=3, distancia_desde_inicio_m=4100, estado=True),
                        Paradero(id_paradero=4, nombre="Mercado 4", tipo="INTERMEDIO", lat=-25.2990, lon=-57.6160, orden_ruta=4, distancia_desde_inicio_m=6800, estado=True),
                        Paradero(id_paradero=5, nombre="Plaza de los Héroes / Microcentro", tipo="INTERMEDIO", lat=-25.2850, lon=-57.6350, orden_ruta=5, distancia_desde_inicio_m=8900, estado=True),
                        Paradero(id_paradero=6, nombre="Terminal Ómnibus Asunción", tipo="TERMINAL", lat=-25.2900, lon=-57.6350, orden_ruta=6, distancia_desde_inicio_m=11500, estado=True),
                    ]
                    for p in paraderos_seed:
                        db.merge(p)

                db.commit()
                logger.info("✅ Flota base y paraderos inicializados con éxito.")
    except Exception as e:
        logger.warning(f"⚠️ Error inicializando seed de datos: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚌 Iniciando Sistema de Microsimulación de Transporte Público...")
    Base.metadata.create_all(bind=engine)
    _ensure_seed_data()

    # ── AVL Streaming: sólo el primer worker que obtenga el lock lo ejecuta ──
    # Con Gunicorn preload_app=True todos los workers comparten el mismo pid al
    # hacer fork, pero cada uno ejecuta su propio lifespan. El lock Redis NX
    # garantiza que solo uno quede activo.
    avl_started = False
    try:
        acquired = _redis_client.set(AVL_LOCK_KEY, "1", nx=True, ex=AVL_LOCK_TTL)
        if acquired:
            logger.info("📡 Este worker obtuvo el lock AVL — iniciando streaming...")
            asyncio.create_task(_start_avl_with_lock_renewal())
            avl_started = True
        else:
            logger.info("ℹ️ Lock AVL en uso por otro worker. Streaming omitido en este proceso.")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo conectar a Redis para lock AVL: {e}. Iniciando AVL sin lock.")
        asyncio.create_task(avl_service.start_streaming())
        avl_started = True

    # ── Sync CID: disparar tarea Celery inmediatamente (no bloquea el startup) ──
    try:
        from tasks.background_tasks import sync_cid_infraestructura
        sync_cid_infraestructura.apply_async(queue="periodic")
        logger.info("⏳ Tarea de sincronización CID enviada a Celery.")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo encolar sync CID en Celery: {e}. Se omite el sync inicial.")

    logger.info("✅ Sistema iniciado.")
    yield

    # Shutdown
    logger.info("🛑 Sistema detenido")
    avl_service.stop()
    if avl_started:
        try:
            _redis_client.delete(AVL_LOCK_KEY)
        except Exception:
            pass


async def _avl_loop():
    """Wrapper que renueva el lock Redis mientras el streaming AVL corre."""
    try:
        while avl_service.running:
            try:
                _redis_client.expire(AVL_LOCK_KEY, AVL_LOCK_TTL)
            except Exception:
                pass
            await asyncio.sleep(AVL_LOCK_TTL // 2)  # renovar a la mitad del TTL
    except asyncio.CancelledError:
        pass

async def _start_avl_with_lock_renewal():
    await asyncio.gather(
        avl_service.start_streaming(),
        _avl_loop(),
        return_exceptions=True,
    )


app = FastAPI(
    title="Sistema de Microsimulación de Transporte Público",
    description="""
    ## API para simulación, monitoreo y análisis operacional del transporte público urbano.
    
    ### Módulos:
    - **AVL**: Posiciones GPS en tiempo real
    - **Simulación**: Motor SimPy para modelado operacional
    - **KPI**: Indicadores operacionales (headway, regularidad, bunching)
    - **Pasajeros**: Simulación de demanda y flujos
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "sistema": "Microsimulador de Transporte Público",
        "version": "1.0.0",
        "estado": "operativo",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
