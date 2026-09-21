"""
Gunicorn configuration for production.
Uses UvicornWorker to run async FastAPI with multiple processes.
Redis lock ensures only one worker starts the AVL streaming task.
"""
import multiprocessing

# --- Binding ---
bind = "0.0.0.0:8000"

# --- Workers ---
workers = min(max(multiprocessing.cpu_count(), 2), 4)
worker_class = "uvicorn.workers.UvicornWorker"

# --- Timeouts ---
# La simulación de UF puede tardar varios minutos (consulta GPS masiva)
timeout = 300          # segundos antes de matar un worker colgado
graceful_timeout = 30  # segundos para terminar requests en curso al reiniciar
keepalive = 5          # segundos para reusar conexiones HTTP keep-alive

# --- Worker tuning ---
worker_connections = 1000  # máx conexiones simultáneas por worker (aplica a uvicorn)
max_requests = 1000         # reciclar worker después de N requests (evita memory leaks)
max_requests_jitter = 100   # offset aleatorio para evitar que todos reciclen a la vez

# --- Logging ---
accesslog = "-"   # stdout
errorlog = "-"    # stdout
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(f)s %(a)s'

# --- Preload ---
# FastAPI con async lifespan requiere preload_app = False para evitar conflictos de event loops en forks
preload_app = False
