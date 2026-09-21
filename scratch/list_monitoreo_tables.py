
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

MON_URL = os.getenv("MONITOREO_DB_URL")

def list_all_tables(url):
    if not url:
        print("No MONITOREO_DB_URL found")
        return
    engine = create_engine(url)
    inspector = inspect(engine)
    for schema in inspector.get_schema_names():
        print(f"Schema: {schema}")
        tables = inspector.get_table_names(schema=schema)
        for table in tables:
            print(f"  - {table}")

if __name__ == "__main__":
    list_all_tables(MON_URL)
