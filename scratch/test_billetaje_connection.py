
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("BILLETAJE_DB_URL")
if not db_url:
    print("No BILLETAJE_DB_URL found in .env")
    exit(1)

print(f"Connecting to {db_url}...")
try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        print("Successfully connected!")
        
        # Consultar columnas de c_transacciones
        query = text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'c_transacciones'
            ORDER BY ordinal_position;
        """)
        result = conn.execute(query)
        columns = result.fetchall()
        
        if not columns:
            print("Table 'c_transacciones' not found or has no columns.")
        else:
            print("\nColumns in 'c_transacciones':")
            for col in columns:
                print(f" - {col[0]} ({col[1]})")
                
        # Ver una muestra de datos
        print("\nSample data (1 row):")
        sample_query = text("SELECT * FROM c_transacciones LIMIT 1;")
        sample_result = conn.execute(sample_query)
        sample = sample_result.fetchone()
        if sample:
            print(sample._asdict())
        else:
            print("No data found in c_transacciones.")

except Exception as e:
    print(f"Error: {e}")
