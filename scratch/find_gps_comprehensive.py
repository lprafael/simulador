
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

CID_URL = os.getenv("CID_DB_URL")
MON_URL = os.getenv("MONITOREO_DB_URL")

def find_gps_tables(url, name):
    print(f"\n--- Checking DB: {name} ---")
    if not url:
        print("No URL")
        return
    try:
        engine = create_engine(url)
        inspector = inspect(engine)
        for schema in inspector.get_schema_names():
            tables = inspector.get_table_names(schema=schema)
            for table in tables:
                if any(x in table.lower() for x in ["gps", "mensaje", "posicion", "avl", "coord"]):
                    print(f"Found in {schema}: {table}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_gps_tables(CID_URL, "CID")
    find_gps_tables(MON_URL, "MONITOREO")
