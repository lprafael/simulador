import logging
from sqlalchemy.orm import Session
from app.models import Linea, Ruta, Paradero, Bus, Simulacion, LineaRutaCatalogo
from app.services.cid_service import cid_service
from typing import List

logger = logging.getLogger(__name__)

class SyncService:
    def sync_infraestructura(self, db: Session, cid_db: Session):
        """
        Sincroniza la infraestructura básica (Líneas, Rutas, Paraderos)
        desde la base de datos del CID a la base de datos local.
        """
        logger.info("🔄 Iniciando sincronización de infraestructura desde CID...")
        
        try:
            # Chequear si ya tenemos datos básicos
            conteo_lineas = db.query(Linea).count()
            
            if conteo_lineas > 0:
                logger.info(f"ℹ️ Infraestructura ya existente ({conteo_lineas} líneas). Saltando sincronización inicial para preservar datos.")
                return

            logger.info("🛠️ Base de datos local vacía. Iniciando poblamiento desde SisCID...")
            # Purgamos tablas de infraestructura para asegurar consistencia (NO tocamos Simulacion)
            for table in [Paradero, Ruta, LineaRutaCatalogo, Linea]:
                try:
                    db.query(table).delete()
                except Exception:
                    db.rollback()
            
            db.commit()
            logger.info("🧹 Tablas de infraestructura limpias.")

            # 2. Obtener líneas desde CID
            lineas_reales = cid_service.get_lineas_reales(cid_db)
            logger.info(f"🔎 Se encontraron {len(lineas_reales)} líneas en el CID.")

            for l_real in lineas_reales:
                # Insertar Línea
                nueva_linea = Linea(
                    id_linea=l_real['id_linea'],
                    numero_linea=l_real['numero_linea'],
                    nombre_comercial=l_real['nombre_comercial'],
                    identificador_troncal=l_real['identificador_troncal'],
                    color_hex=l_real.get('color_hex') or "#3B82F6",
                    estado=l_real.get('estado', True)
                )
                db.add(nueva_linea)
                
                # 2. Sincronizar Rutas por línea
                rutas_reales = cid_service.get_rutas_por_linea(cid_db, l_real['id_linea'])
                for r_idx, r_real in enumerate(rutas_reales):
                    # Generar un ID numérico local para la ruta
                    local_id_ruta = (l_real['id_linea'] * 100) + r_idx 
                    
                    nueva_ruta = Ruta(
                        id_ruta=local_id_ruta,
                        id_linea=l_real['id_linea'],
                        id_externo_cid=r_real['ruta_hex'],
                        nombre=r_real.get('nombre') or f"Línea {l_real['numero_linea']} - {r_real['sentido']}",
                        sentido=r_real['sentido'].upper()
                    )
                    db.add(nueva_ruta)
                    
                    # 3. Sincronizar Paraderos usando el HEX de la ruta
                    paraderos_reales = cid_service.get_paraderos_por_ruta(cid_db, r_real['ruta_hex'])
                    for p_idx, p_real in enumerate(paraderos_reales):
                        nuevo_paradero = Paradero(
                            id_ruta=local_id_ruta,
                            nombre=p_real.get('nombre') or f"Parada {p_idx}",
                            orden_ruta=p_real.get('orden_ruta', p_idx),
                            latitud=p_real['latitud'],
                            longitud=p_real['longitud'],
                            distancia_desde_inicio_m=p_real.get('distancia_m', 0.0)
                        )
                        db.add(nuevo_paradero)
                
                # Commit progresivo: Guardamos cada línea para que sea usable de inmediato
                db.commit()
                logger.info(f"   ∟ ✅ Línea {l_real['numero_linea']} sincronizada ({len(rutas_reales)} rutas)")

            logger.info(f"✅ Sincronización completa: Todas las líneas procesadas.")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error durante la sincronización: {e}")
            raise e

sync_service = SyncService()
