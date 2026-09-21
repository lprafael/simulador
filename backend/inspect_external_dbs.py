import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

CID_URL = os.getenv("CID_DB_URL")
MON_URL = os.getenv("MON_DB_URL") or os.getenv("MONITOREO_DB_URL")

def inspect_db(url, name, schemas=['public']):
    print(f"\n=== INSPECCIONANDO DB: {name} ===")
    try:
        engine = create_engine(url)
        inspector = inspect(engine)
        
        for schema in schemas:
            print(f"\n--- Esquema: {schema} ---")
            tables = inspector.get_table_names(schema=schema)
            for table in tables:
                if table in ['catalogo_rutas', 'eots', 'historico_itinerarios', 'app_monitore_mensajesoperativos'] or schema == 'gestion_uf':
                    print(f"\n[TABLA: {table}]")
                    columns = inspector.get_columns(table, schema=schema)
                    for col in columns:
                        print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")
                    
                    # Ver una muestra (1 fila) si es posible
                    try:
                        with engine.connect() as conn:
                            res = conn.execute(text(f"SELECT * FROM {schema}.{table} LIMIT 1")).fetchone()
                            if res:
                                print(f"  Muestra: {dict(res.items())}")
                    except Exception as e:
                        print(f"  (No se pudo obtener muestra: {e})")
                        
    except Exception as e:
        print(f"Error conectando a {name}: {e}")

if __name__ == "__main__":
    if CID_URL:
        inspect_db(CID_URL, "SisCID", schemas=['public', 'geometria', 'gestion_uf'])
    
    if MON_URL:
        inspect_db(MON_URL, "Monitoreo", schemas=['public'])
