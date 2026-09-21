import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

CID_URL = os.getenv('CID_DB_URL')

def list_ufs():
    if not CID_URL:
        print("No CID_DB_URL")
        return
    
    engine = create_engine(CID_URL)
    with engine.connect() as conn:
        print("--- Unidades Funcionales ---")
        res = conn.execute(text("SELECT id_uf, nombre_uf FROM gestion_uf.unidades_funcionales"))
        for r in res:
            print(f"ID: {r.id_uf}, Nombre: {r.nombre_uf}")
            
        print("\n--- Troncales ---")
        res = conn.execute(text("SELECT id_uf, nombre, es_principal FROM gestion_uf.uf_troncales WHERE activo = TRUE"))
        for r in res:
            print(f"UF_ID: {r.id_uf}, Troncal: {r.nombre}, Principal: {r.es_principal}")

if __name__ == "__main__":
    list_ufs()
