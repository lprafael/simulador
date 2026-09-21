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


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚌 Iniciando Sistema de Microsimulación de Transporte Público...")
    Base.metadata.create_all(bind=engine)

    # ── AVL Streaming: sólo el primer worker que obtenga el lock lo ejecuta ──
    # Con Gunicorn preload_app=True todos los workers comparten el mismo pid al
    # hacer fork, pero cada uno ejecuta su propio lifespan. El lock Redis NX
    # garantiza que solo uno quede activo.
    avl_started = False
    try:
        acquired = _redis_client.set(AVL_LOCK_KEY, "1", nx=True, ex=AVL_LOCK_TTL)
        if acquired:
            logger.info("📡 Este worker obtuvo el lock AVL — iniciando streaming...")
            asyncio.create_task(_avl_loop())
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
