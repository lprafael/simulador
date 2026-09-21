"""
Background Celery tasks.
- sync_cid_infraestructura: sincroniza infraestructura desde CID a la BD local.
  Schedulada cada 30 min por Celery Beat (ver celery_app.py).
"""
import logging
from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.background_tasks.sync_cid_infraestructura",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # segundos entre reintentos
    queue="periodic",
)
def sync_cid_infraestructura(self):
    """
    Sincroniza infraestructura (rutas, paradas, geocercas) desde SisCID
    hacia la BD local del Simulador. Se ejecuta en un proceso Celery
    separado para no bloquear los workers de la API.
    """
    try:
        from app.core.database import SessionLocal, cid_engine
        from app.services.sync_service import sync_service
        from sqlalchemy.orm import sessionmaker

        if not cid_engine:
            logger.warning("CID_DB_URL no configurada. Sync omitido.")
            return {"status": "skipped", "reason": "no CID engine"}

        logger.info("🔄 [Celery] Iniciando sincronización con SisCID...")
        CidSession = sessionmaker(bind=cid_engine)
        db = SessionLocal()
        cid_db = CidSession()
        try:
            sync_service.sync_infraestructura(db, cid_db)
            logger.info("✅ [Celery] Sincronización completada.")
            return {"status": "ok"}
        finally:
            db.close()
            cid_db.close()

    except Exception as exc:
        logger.error(f"❌ [Celery] Error en sync: {exc}")
        raise self.retry(exc=exc)
