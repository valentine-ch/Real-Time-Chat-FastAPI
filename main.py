from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
import jwt
import secrets
import uuid
from connection_manager import ConnectionManager
import schemas


app = FastAPI()
connection_manager = ConnectionManager()
users = dict()
secret_key = secrets.token_hex(256)


def generate_token(user_id):
    token = jwt.encode({'user': user_id}, secret_key, algorithm='HS256')
    return token


def verify_token(token: str):
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = payload['user']
        if user_id not in users:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@app.post("create_user")
async def create_user(username: schemas.Username):
    user_id = str(uuid.uuid4())
    token = generate_token(user_id)
    users[user_id] = username.name
    return {"user_id": user_id, "token": token}


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user_id = verify_token(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    username = users[user_id]
    await connection_manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await connection_manager.broadcast(message, user_id, username)
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
