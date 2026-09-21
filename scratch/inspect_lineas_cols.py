import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

inspector = inspect(engine)
columns = inspector.get_columns('lineas', schema='public')

print("Columnas detectadas en public.lineas:")
for col in columns:
    print(f"- {col['name']} ({col['type']})")
