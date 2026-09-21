import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

CID_URL = os.getenv('CID_DB_URL')

def check_col():
    if not CID_URL:
        print("No CID_DB_URL")
        return
    
    engine = create_engine(CID_URL)
    with engine.connect() as conn:
        # Query geography_columns or geometry_columns
        res = conn.execute(text("SELECT type, srid FROM geometry_columns WHERE f_table_schema = 'geometria' AND f_table_name = 'geocercas'"))
        row = res.fetchone()
        if row:
            print(f"Tipo: {row[0]}, SRID: {row[1]}")
        else:
            print("No se encontró información en geometry_columns")

if __name__ == "__main__":
    check_col()
