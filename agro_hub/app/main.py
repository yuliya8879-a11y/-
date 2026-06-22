import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s"
)
logger = logging.getLogger(__name__)

from .database import engine, Base
from .routers import contacts, lots, messages, dashboard

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Agro Hub AI Manager запускается...")
    yield
    logger.info("Agro Hub AI Manager останавливается...")


app = FastAPI(
    title="Agro Hub AI Manager",
    description="AI-менеджер для сбора лотов в агробизнесе",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(contacts.router)
app.include_router(lots.router)
app.include_router(messages.router)
app.include_router(dashboard.router)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Agro Hub AI Manager API работает"}


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    from .telegram_bot import process_webhook_update
    try:
        await process_webhook_update(data)
    except Exception as e:
        logger.error(f"Ошибка обработки Telegram webhook: {e}", exc_info=True)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Agro Hub AI Manager"}
