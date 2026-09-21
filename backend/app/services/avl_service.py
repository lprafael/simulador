import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.websocket.manager import manager
import asyncio
import logging

logger = logging.getLogger(__name__)

class AvlInboundService:
    """
    Servicio que lee mensajes operativos de la BD de Monitoreo
    y los retransmite vía WebSocket al Dashboard.
    """
    
    def __init__(self, monitoreo_db_factory):
        self.get_monitoreo_db = monitoreo_db_factory
        self.running = False

    async def start_streaming(self):
        self.running = True
        logger.info("📡 Iniciando streaming de AVL desde BD Monitoreo...")
        
        ultima_id = 0
        
        while self.running:
            try:
                # Usar un generador de sesión manual para evitar fugas
                db = next(self.get_monitoreo_db())
                if not db:
                    await asyncio.sleep(10)
                    continue
                
                # Consultar nuevos mensajes (polling cada 5 segundos para demo)
                # En producción se podría usar LISTEN/NOTIFY o un CDC
                query = text("""
                    SELECT 
                        id, mean_id, agency_id, route_id, 
                        latitude, longitude, velocidad, rumbo, fecha_hora
                    FROM public.app_monitoreo_mensajeoperativo
                    WHERE id > :ultima_id
                    ORDER BY id ASC
                    LIMIT 50
                """)
                
                result = db.execute(query, {"ultima_id": ultima_id}).fetchall()
                
                for row in result:
                    msg = dict(row._asdict())
                    ultima_id = msg['id']
                    
                    # Formatear para el frontend
                    payload = {
                        "tipo": "POSICION_GPS",
                        "datos": {
                            "id_bus": msg['mean_id'],
                            "id_empresa": msg['agency_id'],
                            "id_ruta": msg['route_id'],
                            "lat": msg['latitude'],
                            "lon": msg['longitude'],
                            "velocidad": msg['velocidad'],
                            "rumbo": msg['rumbo'],
                            "timestamp": msg['fecha_hora'].isoformat() if msg['fecha_hora'] else None
                        }
                    }
                    
                    # Emitir a todos los clientes conectados
                    await manager.broadcast(payload)
                
                db.close()
                await asyncio.sleep(5) # Intervalo de polling
                
            except Exception as e:
                logger.error(f"❌ Error en streaming AVL: {e}")
                await asyncio.sleep(10)

    def stop(self):
        self.running = False

# El servicio se iniciará en main.py durante el lifespan de la app
