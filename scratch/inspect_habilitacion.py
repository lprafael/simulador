import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
inspector = inspect(engine)

schema = 'registro_habilitacion'
try:
    tables = inspector.get_table_names(schema=schema)
    print(f"Tablas en {schema}: {tables}")
    for table in tables:
        columns = inspector.get_columns(table, schema=schema)
        print(f"\n--- Tabla: {table} ---")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
except Exception as e:
    print(f"Error inspeccionando {schema}: {e}")
