import os
import sys
import time
import socket
import urllib.request
import urllib.error
from urllib.parse import urlparse
import json

def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def test_tcp_socket(host, port, timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, int(port)))
        s.close()
        return True, "Puerto accesible"
    except Exception as e:
        return False, str(e)

def test_database_url(name, url, sample_queries=None, timeout=10):
    print(f"\n--- Probando {name} ---")
    if not url:
        print("❌ Variable no configurada o vacía.")
        return False
    
    # Parse host and port for pre-flight check
    try:
        parsed = urlparse(url)
        # Handle passwords with special characters in raw url
        user_host = url.split("@")[-1].split("/")[0]
        if ":" in user_host:
            host, port = user_host.split(":")
        else:
            host, port = user_host, 5432
    except Exception as ep:
        host, port = None, None

    if host and port:
        print(f"  [1/2] Verificando socket TCP ({host}:{port})...")
        ok, msg = test_tcp_socket(host, port, timeout=min(timeout, 5))
        if ok:
            print(f"  ✅ Socket TCP abierto: {host}:{port}")
        else:
            print(f"  ❌ Socket TCP falló en {host}:{port}: {msg}")
            return False

    print(f"  [2/2] Conectando a PostgreSQL...")
    try:
        from sqlalchemy import create_engine, text
        # Añadir connect_timeout
        engine_args = {}
        if "postgresql" in url:
            engine_args["connect_args"] = {"connect_timeout": timeout}
        engine = create_engine(url, **engine_args)
        
        t0 = time.time()
        with engine.connect() as conn:
            elapsed = time.time() - t0
            version = conn.execute(text("SELECT version()")).scalar()
            print(f"  ✅ Conexión exitosa ({elapsed:.2f}s)!")
            print(f"     Versión: {version.split(',')[0] if version else 'N/A'}")
            
            if sample_queries:
                for q_name, q_sql in sample_queries.items():
                    try:
                        res = conn.execute(text(q_sql)).fetchall()
                        print(f"     📊 {q_name}: {res}")
                    except Exception as eq:
                        print(f"     ⚠️ {q_name}: error ejecutando consulta ({eq})")
        return True
    except Exception as e:
        print(f"  ❌ Error de conexión a {name}: {e}")
        return False

def test_redis(redis_url, timeout=5):
    print(f"\n--- Probando Redis ({redis_url}) ---")
    if not redis_url:
        print("❌ REDIS_URL no configurada.")
        return False
    
    try:
        import redis
        r = redis.from_url(redis_url, socket_timeout=timeout)
        t0 = time.time()
        pong = r.ping()
        elapsed = time.time() - t0
        if pong:
            info = r.info("server")
            redis_ver = info.get("redis_version", "desconocida")
            r.set("test:healthcheck", "OK", ex=10)
            val = r.get("test:healthcheck")
            val_str = val.decode() if isinstance(val, bytes) else str(val)
            print(f"  ✅ Conexión exitosa a Redis ({elapsed*1000:.1f}ms)!")
            print(f"     Versión Redis: {redis_ver}")
            print(f"     Test SET/GET: {val_str}")
            return True
        else:
            print(f"  ❌ Ping a Redis no respondió True.")
            return False
    except Exception as e:
        print(f"  ❌ Error conectando a Redis: {e}")
        return False

def test_waze_ccp(feed_url, api_key):
    print(f"\n--- Probando Waze CCP Feed ---")
    print(f"  URL: {feed_url}")
    print(f"  API Key: {'Configurada' if api_key else 'NO configurada (vacía)'}")
    
    if not feed_url:
        print("❌ WAZE_CCP_FEED_URL no configurada.")
        return False

    headers = {
        "User-Agent": "SimuladorTransporte/1.0"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(feed_url, headers=headers)
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=10) as response:
            elapsed = time.time() - t0
            print(f"  ✅ Waze CCP Feed respondió HTTP {response.status} en {elapsed:.2f}s!")
            data = response.read(200)
            print(f"     Primeros bytes: {data[:100]}...")
            return True
    except urllib.error.HTTPError as he:
        print(f"  ℹ️ Respuesta HTTP de Waze: {he.code} {he.reason}")
        if he.code in [401, 403]:
            print("     (Esperable si la API Key está vacía o pendiente de autorización por Waze for Cities)")
        return False
    except Exception as e:
        print(f"  ❌ Error consultando Waze Feed: {e}")
        return False

def test_carto(carto_key):
    print(f"\n--- Probando CARTO Basemaps / API Key ---")
    print(f"  CARTO Key: {carto_key}")
    # Probar endpoint de basemap CartoDB Positron
    url = f"https://basemaps.cartocdn.com/rastertiles/voyager/0/0/0.png"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=8) as resp:
            elapsed = time.time() - t0
            print(f"  ✅ Servidor de mapas CARTO accesible (HTTP {resp.status}, {elapsed*1000:.1f}ms).")
            return True
    except Exception as e:
        print(f"  ❌ Error accediendo a CARTO: {e}")
        return False

def main():
    print_header("DIAGNÓSTICO Y PRUEBA DE CONEXIONES (.env)")
    
    # Cargar variables de entorno
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    results = {}

    # 1. Base de datos local (DATABASE_URL)
    local_db = os.getenv("DATABASE_URL")
    results["BD Local (PostgreSQL)"] = test_database_url(
        "BD Local (DATABASE_URL)",
        local_db,
        sample_queries={
            "Extensión PostGIS": "SELECT PostGIS_Version();",
            "Conteo Buses": "SELECT count(*) FROM buses;",
            "Conteo Líneas": "SELECT count(*) FROM lineas;",
            "Conteo Rutas": "SELECT count(*) FROM rutas;",
            "Conteo Paraderos": "SELECT count(*) FROM paraderos;",
            "Conteo Empresas": "SELECT count(*) FROM empresas;"
        }
    )

    # 2. Redis local (REDIS_URL)
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    results["Cache & Colas (Redis)"] = test_redis(redis_url)

    # 3. BD SisCID (CID_DB_URL)
    cid_db = os.getenv("CID_DB_URL")
    results["BD SisCID (168.90.177.232)"] = test_database_url(
        "BD SisCID (CID_DB_URL)",
        cid_db,
        sample_queries={
            "Líneas activas": "SELECT count(*) FROM public.lineas WHERE estado = true;",
            "UFs": "SELECT count(*) FROM gestion_uf.unidades_funcionales;",
            "Rutas en catálogo": "SELECT count(*) FROM public.catalogo_rutas;"
        },
        timeout=10
    )

    # 4. BD Monitoreo (MONITOREO_DB_URL)
    mon_db = os.getenv("MONITOREO_DB_URL")
    results["BD Monitoreo (monitoreo.vmt.gov.py)"] = test_database_url(
        "BD Monitoreo (MONITOREO_DB_URL)",
        mon_db,
        sample_queries={
            "Último ID y Fecha en app_monitoreo_mensajeoperativo": """
                SELECT max(id) as max_id, max(fecha_hora) as ultima_fecha 
                FROM public.app_monitoreo_mensajeoperativo;
            """
        },
        timeout=10
    )

    # 5. BD Billetaje (BILLETAJE_DB_URL)
    billetaje_db = os.getenv("BILLETAJE_DB_URL")
    results["BD Billetaje (192.168.174.21)"] = test_database_url(
        "BD Billetaje (BILLETAJE_DB_URL)",
        billetaje_db,
        sample_queries={
            "Columnas en c_transacciones": "SELECT column_name FROM information_schema.columns WHERE table_name = 'c_transacciones' LIMIT 5;"
        },
        timeout=5
    )

    # 6. Waze CCP Feed
    waze_url = os.getenv("WAZE_CCP_FEED_URL")
    waze_key = os.getenv("WAZE_API_KEY")
    results["Waze CCP Feed"] = test_waze_ccp(waze_url, waze_key)

    # 7. CARTO Basemaps
    carto_key = os.getenv("VITE_CARTO_API_KEY")
    results["CARTO Basemaps"] = test_carto(carto_key)

    # Resumen final
    print_header("RESUMEN DE ESTADO DE CONEXIONES")
    for serv, ok in results.items():
        estado = "✅ CONECTADO / OPERATIVO" if ok else "⚠️ NO DISPONIBLE / REQUIERE ATENCIÓN"
        print(f"  {serv:<40} : {estado}")
    print("=" * 70)

if __name__ == "__main__":
    main()
