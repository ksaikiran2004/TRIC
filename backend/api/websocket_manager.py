"""
TRIC - WebSocket Manager
Handles live streaming of sensor triggers and drone paths to the UI.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict

class ConnectionManager:
    def __init__(self):
        # Keeps track of all active browser/dashboard connections
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict):
        """
        Sends data (like new sensor hits) to every connected dashboard.
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # If a connection drops, we ignore it and keep broadcasting
                pass

# Initialize the manager globally
manager = ConnectionManager()