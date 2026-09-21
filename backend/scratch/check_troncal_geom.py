import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

CID_URL = os.getenv('CID_DB_URL')

def check_geom():
    if not CID_URL:
        print("No CID_DB_URL")
        return
    
    engine = create_engine(CID_URL)
    with engine.connect() as conn:
        res = conn.execute(text("SELECT ST_GeometryType(geom), ST_AsText(geom) as wkt FROM gestion_uf.uf_troncales LIMIT 1"))
        row = res.fetchone()
        if row:
            print(f"Tipo Geometría: {row[0]}")
            print(f"Muestra WKT: {row[1][:100]}...")
        else:
            print("No hay troncales con geometría.")

if __name__ == "__main__":
    check_geom()
