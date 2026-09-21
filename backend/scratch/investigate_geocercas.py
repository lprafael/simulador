import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

CID_URL = os.getenv('CID_DB_URL')

def investigate():
    if not CID_URL:
        print("No CID_DB_URL")
        return
    
    engine = create_engine(CID_URL)
    with engine.connect() as conn:
        print("--- Contar registros en geometria.geocercas por id_tipo ---")
        res = conn.execute(text("SELECT id_tipo, COUNT(*) FROM geometria.geocercas GROUP BY id_tipo"))
        for r in res:
            print(f"Tipo: {r.id_tipo}, Cantidad: {r.count}")
            
        print("\n--- Verificar relación entre uf_troncales y geocercas ---")
        res = conn.execute(text("""
            SELECT t.id_troncal, t.nombre, g.id_geocerca, g.id_tipo
            FROM gestion_uf.uf_troncales t
            JOIN geometria.geocercas g ON t.id_troncal = g.id_troncal_uf
            LIMIT 10
        """))
        rows = res.fetchall()
        if rows:
            for r in rows:
                print(f"Troncal ID: {r.id_troncal} ({r.nombre}) -> Geocerca ID: {r.id_geocerca} (Tipo: {r.id_tipo})")
        else:
            print("No se encontraron registros vinculados por id_troncal_uf en geocercas.")

        print("\n--- ¿Tienen geometría las uf_troncales directamente? ---")
        res = conn.execute(text("SELECT id_troncal, nombre, (geom IS NOT NULL) as tiene_geom FROM gestion_uf.uf_troncales LIMIT 5"))
        for r in res:
            print(f"Troncal: {r.nombre}, ¿Tiene Geom?: {r.tiene_geom}")

if __name__ == "__main__":
    investigate()
