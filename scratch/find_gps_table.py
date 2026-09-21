
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()

MON_URL = os.getenv("MONITOREO_DB_URL")

def find_table(url, search):
    if not url: return
    engine = create_engine(url)
    inspector = inspect(engine)
    for schema in inspector.get_schema_names():
        for table in inspector.get_table_names(schema=schema):
            if search in table:
                print(f"Found: {schema}.{table}")

if __name__ == "__main__":
    find_table(MON_URL, "mensajes")
    find_table(MON_URL, "posicion")
    find_table(MON_URL, "gps")
    find_table(MON_URL, "avl")
