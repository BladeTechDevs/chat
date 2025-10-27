from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from database import SessionLocal, User, Message
from datetime import datetime

router = APIRouter()
SECRET_KEY = "clave_super_secreta"
ALGORITHM = "HS256"

connections = {}

@router.websocket("/ws/{token}")
async def chat(websocket: WebSocket, token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            await websocket.close()
            return
    except JWTError:
        await websocket.close()
        return

    await websocket.accept()
    connections[username] = websocket

    db = SessionLocal()
    print(f"{username} conectado.")

    try:
        while True:
            data = await websocket.receive_text()
            # Guardar mensaje en DB
            user = db.query(User).filter(User.username == username).first()
            msg = Message(content=data, user_id=user.id, timestamp=datetime.utcnow())
            db.add(msg)
            db.commit()

            # Enviar mensaje a todos los conectados
            for user_ws in connections.values():
                await user_ws.send_text(f"{username}: {data}")
    except WebSocketDisconnect:
        del connections[username]
        print(f"{username} desconectado.")
        db.close()
