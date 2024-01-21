from fastapi import WebSocket
import time
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str, room, user_id: str, username: str):
        content = {
            "user": {
                "id": user_id,
                "name": username
            },
            "text": message,
            "room": room,
            "timestamp": int(time.time() * 1000)
        }
        for connection in self.active_connections:
            await connection.send_text(json.dumps(content))
