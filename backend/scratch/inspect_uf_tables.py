import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load from root .env
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

CID_URL = os.getenv('CID_DB_URL')
MON_URL = os.getenv('MONITOREO_DB_URL')
BIL_URL = os.getenv('BILLETAJE_DB_URL')

def inspect():
    if CID_URL:
        engine = create_engine(CID_URL)
        with engine.connect() as conn:
            print("--- Columns of gestion_uf.uf_troncales ---")
            res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'gestion_uf' AND table_name = 'uf_troncales'"))
            for r in res:
                print(f"{r.column_name}: {r.data_type}")
                
            print("\n--- Columns of geometria.geocercas ---")
            res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'geometria' AND table_name = 'geocercas'"))
            for r in res:
                print(f"{r.column_name}: {r.data_type}")

            print("\n--- Columns of gestion_uf.composicion_uf ---")
            res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'gestion_uf' AND table_name = 'composicion_uf'"))
            for r in res:
                print(f"{r.column_name}: {r.data_type}")

    if BIL_URL:
        print("\nConnecting to Billetaje DB...")
        engine_bil = create_engine(BIL_URL)
        with engine_bil.connect() as conn:
            print("--- Columns of c_transacciones (Billetaje) ---")
            query = text("""
                SELECT table_schema, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'c_transacciones'
                ORDER BY table_schema, ordinal_position;
            """)
            res = conn.execute(query)
            for r in res:
                print(f"{r.table_schema}.{r.column_name}: {r.data_type}")
    else:
        print("No BILLETAJE_DB_URL found")

if __name__ == "__main__":
    inspect()
