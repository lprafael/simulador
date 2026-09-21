import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

CID_URL = os.getenv("CID_DB_URL")
MON_URL = os.getenv("MON_DB_URL") or os.getenv("MONITOREO_DB_URL")

def inspect_table(engine, schema, table):
    print(f"\n[TABLA: {schema}.{table}]")
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table, schema=schema)
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Muestra rápida
        with engine.connect() as conn:
            query = f"SELECT * FROM {schema}.{table} LIMIT 1"
            res = conn.execute(text(query)).fetchone()
            if res:
                # Usamos _asdict() si está disponible en la fila de SQLAlchemy 1.4+
                try:
                    print(f"  Muestra: {res._asdict()}")
                except:
                    print(f"  Muestra: {res}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    if CID_URL:
        engine_cid = create_engine(CID_URL)
        print("\n=== ESTRUCTURA SisCID ===")
        inspect_table(engine_cid, 'public', 'catalogo_rutas')
        inspect_table(engine_cid, 'public', 'eots')
        inspect_table(engine_cid, 'geometria', 'historico_itinerarios')
        
        # Listar todas las de gestion_uf
        inspector = inspect(engine_cid)
        for t in inspector.get_table_names(schema='gestion_uf'):
            inspect_table(engine_cid, 'gestion_uf', t)
            
    if MON_URL:
        engine_mon = create_engine(MON_URL)
        print("\n=== ESTRUCTURA Monitoreo ===")
        # El usuario dijo: app_monitore_mensajesoperativos
        # Podría estar en public u otro esquema. Vamos a buscarla.
        inspector_mon = inspect(engine_mon)
        found = False
        for schema in inspector_mon.get_schema_names():
            if 'app_monitore_mensajesoperativos' in inspector_mon.get_table_names(schema=schema):
                inspect_table(engine_mon, schema, 'app_monitore_mensajesoperativos')
                found = True
        if not found:
            print("  No se encontró la tabla app_monitore_mensajesoperativos")
