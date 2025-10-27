from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from database import init_db
from auth import router as auth_router
from chat import router as chat_router

app = FastAPI()

init_db()

app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
