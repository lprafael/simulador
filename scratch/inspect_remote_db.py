import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

# Probamos con la URL del CID que está en el .env
CID_URL = os.getenv("CID_DB_URL")
if not CID_URL:
    print("Error: No se encontró CID_DB_URL en el .env")
    exit(1)

print(f"Conectando a base de datos remota: {CID_URL.split('@')[-1]}")
engine = create_engine(CID_URL)

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema='public')
    print(f"Tablas encontradas en public: {tables}")
    
    if 'lineas' in tables:
        columns = inspector.get_columns('lineas', schema='public')
        print("Columnas en public.lineas (Remota):")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")
    else:
        print("La tabla 'lineas' NO existe en la base de datos remota.")
except Exception as e:
    print(f"Error al conectar o inspeccionar: {e}")
