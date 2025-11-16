# app/loader.py

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import httpx
from loguru import logger

from app.config import config
from app.handlers import register_all_handlers


# ===== Bot va Dispatcher =====
bot = Bot(
    token=config.telegram.bot_token,
    default=DefaultBotProperties(parse_mode="HTML"),
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ===== ERPNext uchun HTTP klient =====
http_client = httpx.AsyncClient(
    base_url=config.erp.base_url,
    headers={
        "Authorization": f"token {config.erp.api_key}:{config.erp.api_secret}"
    },
    timeout=15.0,
    follow_redirects=True,
)


# ===== STARTUP / SHUTDOWN =====
async def on_startup():
    """
    FastAPI server ishga tushayotganda chaqiriladi.
    Shu yerda barcha routerlarni Dispatcher'ga ulab qo'yamiz.
    """
    # 🔥 ENG MUHIM QATOR: /start, passport, menu, contract, payments va h.k.
    # hammasi shu yerda DP ga ulanadi
    register_all_handlers(dp)

    logger.info("Webhook bot ishga tushdi!")
    logger.info(f"ERPNext Base URL: {config.erp.base_url}")


async def on_shutdown():
    """
    Server yopilganda resurslarni tozalash.
    """
    logger.warning("Bot to‘xtatilmoqda…")
    await http_client.aclose()
    await bot.session.close()
    logger.success("Bot muvaffaqiyatli to‘xtatildi.")
