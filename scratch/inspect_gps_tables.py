
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

CID_URL = os.getenv("CID_DB_URL")

def inspect_table(url, schema, table):
    print(f"\n--- Table: {schema}.{table} ---")
    engine = create_engine(url)
    inspector = inspect(engine)
    cols = inspector.get_columns(table, schema=schema)
    for c in cols:
        print(f"  {c['name']}: {c['type']}")
    
    with engine.connect() as conn:
        res = conn.execute(text(f"SELECT * FROM {schema}.{table} LIMIT 1")).fetchone()
        print(f"  Sample: {res}")

if __name__ == "__main__":
    inspect_table(CID_URL, "public", "posiciones_gps")
    inspect_table(CID_URL, "public", "app_monitoreo_mensajeoperativo")
