from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
import jwt
import secrets
import uuid
import json
from connection_manager import ConnectionManager
import schemas


app = FastAPI()
connection_manager = ConnectionManager()
users = dict()
secret_key = secrets.token_hex(256)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


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


@app.post("/create_user")
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
            message_raw = await websocket.receive_text()
            message = json.loads(message_raw)
            await connection_manager.broadcast(message["text"], message["room"], user_id, username)
    except json.JSONDecodeError:
        pass
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
