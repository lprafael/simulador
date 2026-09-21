import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

CID_URL = os.getenv('CID_DB_URL')

def generate_geofences():
    if not CID_URL:
        logger.error("No CID_DB_URL found")
        return
    
    engine = create_engine(CID_URL)
    
    # SQL para generar e insertar los buffers
    # Usamos ST_Buffer sobre geography para que el radio sea en metros (50m)
    # Eliminamos ST_Multi porque la columna en CID es tipo POLYGON
    query = text("""
        INSERT INTO geometria.geocercas (id_tipo, geom, id_troncal_uf, fecha_creacion, fecha_actualizacion)
        SELECT 
            7 as id_tipo,
            ST_Buffer(geom::geography, 50)::geometry as geom,
            id_troncal as id_troncal_uf,
            NOW() as fecha_creacion,
            NOW() as fecha_actualizacion
        FROM gestion_uf.uf_troncales
        WHERE activo = TRUE
          AND geom IS NOT NULL
          AND id_troncal NOT IN (
              SELECT id_troncal_uf FROM geometria.geocercas 
              WHERE id_tipo = 7 AND id_troncal_uf IS NOT NULL
          )
        RETURNING id_geocerca;
    """)
    
    try:
        with engine.begin() as conn:
            result = conn.execute(query)
            ids = [r[0] for r in result]
            logger.info(f"✅ Se han generado {len(ids)} geocercas para troncales (Tipo 7).")
            if ids:
                logger.info(f"IDs de geocercas creadas: {ids}")
            else:
                logger.info("No se generaron nuevas geocercas (posiblemente ya existían o no hay troncales activas).")
    except Exception as e:
        logger.error(f"❌ Error generando geocercas: {e}")

if __name__ == "__main__":
    generate_geofences()
