from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.getenv('CID_DB_URL'))
try:
    with engine.connect() as conn:
        res = conn.execute(text('SELECT * FROM public.eots LIMIT 1')).fetchone()
        if res:
            # En SQLAlchemy 1.4+ las filas tienen _asdict() o se pueden convertir a dict
            print(f"EOT Sample: {dict(res._mapping)}")
        else:
            print("EOT Sample: None")
except Exception as e:
    print(f"Error: {e}")
