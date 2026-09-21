import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Sincronizando esquema en: {DATABASE_URL.split('@')[-1]}")

engine = create_engine(DATABASE_URL)

alter_queries = [
    "ALTER TABLE public.lineas ADD COLUMN IF NOT EXISTS id_uf INTEGER;",
    "ALTER TABLE public.lineas ADD COLUMN IF NOT EXISTS color_hex VARCHAR(7) DEFAULT '#3B82F6';",
    "ALTER TABLE public.lineas ADD COLUMN IF NOT EXISTS creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;"
]

with engine.connect() as conn:
    for query in alter_queries:
        try:
            conn.execute(text(query))
            conn.commit()
            print(f"Ejecutado: {query}")
        except Exception as e:
            print(f"Error en {query}: {e}")

print("Sincronización remota completada.")
