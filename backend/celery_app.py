"""
Celery application for background tasks.
Broker: Redis (already in docker-compose).
Tasks: periodic CID sync, heavy analysis jobs offloaded from the API.
"""
import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Usar base de datos 1 para Celery (0 puede usarla la app)
celery_app = Celery(
    "simulador",
    broker=REDIS_URL.replace("/0", "/1"),
    backend=REDIS_URL.replace("/0", "/1"),
    include=["tasks.background_tasks"],
)

celery_app.conf.update(
    # Serialización
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone (Paraguay no observa DST)
    timezone="America/Asuncion",
    enable_utc=True,

    # Reintentos automáticos ante fallos transitorios de BD
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Limitar concurrencia: el sync con CID es I/O pesado, no CPU
    worker_concurrency=2,
    worker_prefetch_multiplier=1,  # un task a la vez por worker (evita acumulación)

    # Resultados: expirar tras 1 hora (no los necesitamos persitidos)
    result_expires=3600,

    # ── Tareas periódicas (Celery Beat) ──────────────────────────────────────
    beat_schedule={
        # Sincronizar infraestructura desde CID cada 30 minutos
        "sync-cid-infraestructura": {
            "task": "tasks.background_tasks.sync_cid_infraestructura",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "periodic"},
        },
    },
)
