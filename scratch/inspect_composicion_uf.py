import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))
inspector = inspect(engine)
try:
    columns = inspector.get_columns('composicion_uf', schema='public')
    print('Columnas en composicion_uf:')
    for c in columns:
        print(f"- {c['name']} ({c['type']})")
except Exception as e:
    print(f"Error: {e}")
