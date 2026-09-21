import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

CID_URL = os.getenv('CID_DB_URL')

def check_types():
    if not CID_URL:
        print("No CID_DB_URL")
        return
    
    engine = create_engine(CID_URL)
    with engine.connect() as conn:
        print("--- Tipos de Geocerca ---")
        res = conn.execute(text("SELECT * FROM geometria.tipos_geocerca"))
        for r in res:
            print(f"ID: {r.id_tipo}, Descripción: {r.descripcion}")

if __name__ == "__main__":
    check_types()
