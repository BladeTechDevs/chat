from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from database import SessionLocal, User, Message
from datetime import datetime
from rsa_utils import load_keys, encrypt_rsa, decrypt_rsa
from sqlalchemy.orm import Session

router = APIRouter()
SECRET_KEY = "clave_super_secreta"
ALGORITHM = "HS256"

connections = {}
private_key, public_key = load_keys()  # 🔑 Cargamos las claves RSA

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

            # 🔒 Cifrar mensaje con clave pública antes de guardar
            encrypted_data = encrypt_rsa(data, public_key)

            user = db.query(User).filter(User.username == username).first()
            msg = Message(content=encrypted_data.hex(), user_id=user.id, timestamp=datetime.utcnow())
            db.add(msg)
            db.commit()

            # 💬 Enviar mensaje normal (no cifrado) a los demás conectados
            for user_ws in connections.values():
                await user_ws.send_text(f"{username}: {data}")
    except WebSocketDisconnect:
        del connections[username]
        print(f"{username} desconectado.")
        db.close()


