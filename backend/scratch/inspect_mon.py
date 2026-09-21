import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

MON_URL = os.getenv('MONITOREO_DB_URL')

def inspect_mon():
    if not MON_URL:
        print("No MONITOREO_DB_URL")
        return
    
    engine = create_engine(MON_URL)
    inspector = inspect(engine)
    
    table_name = 'app_monitoreo_mensajeoperativo'
    found = False
    for schema in inspector.get_schema_names():
        if table_name in inspector.get_table_names(schema=schema):
            print(f"Found {table_name} in schema: {schema}")
            columns = inspector.get_columns(table_name, schema=schema)
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            found = True
            break
            
    if not found:
        print(f"Table {table_name} not found")

if __name__ == "__main__":
    inspect_mon()
