import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))

queries = [
    "ALTER TABLE public.composicion_uf ADD COLUMN IF NOT EXISTS id_linea INTEGER;"
]

with engine.begin() as conn:
    for q in queries:
        conn.execute(text(q))
        print(f"Ejecutado: {q}")

print("Columna id_linea asegurada en composicion_uf remota.")
