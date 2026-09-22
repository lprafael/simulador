"""
WebSocket Manager para transmisión de eventos en tiempo real.
Gestiona conexiones múltiples de clientes y broadcasting de mensajes.
"""

import json
import asyncio
import logging
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

ws_router = APIRouter()

class ConnectionManager:
    """Gestiona las conexiones WebSocket activas."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, room: str = "general"):
        # IMPORTANTE: accept() debe ser lo primero
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)
        self.all_connections.add(websocket)
        logger.info(f"WebSocket conectado. Room: {room}. Total: {len(self.all_connections)}")

    def disconnect(self, websocket: WebSocket, room: str = "general"):
        if room in self.active_connections:
            try:
                self.active_connections[room].remove(websocket)
            except ValueError:
                pass
        self.all_connections.discard(websocket)
        logger.info(f"WebSocket desconectado. Total: {len(self.all_connections)}")

    async def send_personal(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.debug(f"No se pudo enviar mensaje personal (cliente desconectado): {e}")

    async def broadcast(self, message: dict, room: str = "general"):
        """Envía un mensaje a todos los clientes en una sala."""
        connections = self.active_connections.get(room, [])
        if not connections:
            return
            
        message_str = json.dumps(message)
        dead_connections = []
        
        for connection in list(connections):
            try:
                await connection.send_text(message_str)
            except Exception:
                dead_connections.append(connection)
        
        for dead in dead_connections:
            self.disconnect(dead, room)

    async def broadcast_all(self, message: dict):
        """Envía un mensaje a todas las conexiones activas."""
        message_str = json.dumps(message)
        dead = []
        for conn in list(self.all_connections):
            try:
                await conn.send_text(message_str)
            except Exception:
                dead.append(conn)
        for d in dead:
            self.all_connections.discard(d)

# Singleton manager
manager = ConnectionManager()

# Store de posiciones simuladas en memoria
posiciones_en_tiempo_real: Dict[int, dict] = {}

@ws_router.websocket("/ws/posiciones")
async def websocket_posiciones(websocket: WebSocket):
    """WebSocket para posiciones GPS en tiempo real."""
    await manager.connect(websocket, "posiciones")
    try:
        # Enviar confirmación inmediata y posiciones activas
        await manager.send_personal({
            "tipo": "CONEXION_OK",
            "mensaje": "Conectado al stream de posiciones GPS",
            "timestamp": datetime.utcnow().isoformat(),
        }, websocket)

        if posiciones_en_tiempo_real:
            await manager.send_personal({
                "tipo": "HEARTBEAT",
                "posiciones": list(posiciones_en_tiempo_real.values()),
                "timestamp": datetime.utcnow().isoformat(),
            }, websocket)
        
        while True:
            # Mantener viva la conexión y esperar PINGs del cliente
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                if msg.get("tipo") == "PING":
                    await manager.send_personal({
                        "tipo": "PONG",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "posiciones")
    except Exception as e:
        logger.error(f"Error en socket de posiciones: {e}")
        manager.disconnect(websocket, "posiciones")
