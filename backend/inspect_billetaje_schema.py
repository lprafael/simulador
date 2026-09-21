
from sqlalchemy import create_engine, text
import os
from app.core.config import settings

def inspect_billetaje():
    url = settings.BILLETAJE_DB_URL
    if not url:
        print("No BILLETAJE_DB_URL found")
        return
        
    print(f"Connecting to Billetaje DB...")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print("Connected!")
            # Buscar tabla c_transacciones en todos los esquemas
            query = text("""
                SELECT table_schema, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'c_transacciones'
                ORDER BY table_schema, ordinal_position;
            """)
            result = conn.execute(query)
            columns = result.fetchall()
            
            print(f"Total columns found: {len(columns)}")
            for schema, col, dtype in columns:
                print(f"{schema}.c_transacciones.{col} ({dtype})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_billetaje()
