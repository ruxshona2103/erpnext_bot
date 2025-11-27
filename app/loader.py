"""
Bot Loader - Initialization module

Bu modul bot'ning asosiy komponentlarini yaratadi:
- Bot instance
- Dispatcher with RedisStorage
- Event handlers

Nima uchun RedisStorage?
------------------------
- Persistent storage: Server restart bo'lganda ma'lumotlar saqlanadi
- User state management: Conversation flow saqlanadi
- Production ready: Real bot'lar uchun mo'ljallangan

Architecture:
-------------
- Bot: Telegram API bilan ishlash
- Dispatcher: Message routing va handler management
- RedisStorage: FSM state va ma'lumotlarni saqlash
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from loguru import logger

from app.config import config
from app.handlers import register_all_handlers


# ============================================================================
# BOT INITIALIZATION
# ============================================================================

# Bot instance - Telegram API bilan ishlash uchun
# parse_mode="HTML" - Barcha xabarlarda HTML formatlash ishlaydi
bot = Bot(
    token=config.telegram.bot_token,
    default=DefaultBotProperties(parse_mode="HTML"),
)


# ============================================================================
# REDIS STORAGE CONFIGURATION
# ============================================================================

# Redis connection
# Nima uchun async Redis?
# - aiogram async framework - blocking I/O bo'lmasligi kerak
# - Barcha operatsiyalar async (await)
redis = Redis(
    host=config.redis.host,
    port=config.redis.port,
    db=config.redis.db,
    decode_responses=True,  # String'larni avtomatik decode qilish
)

# RedisStorage - aiogram FSM uchun
# Bu yerda barcha user state'lar va ma'lumotlar saqlanadi:
# - Conversation state (qaysi bosqichda)
# - User data (vaqtincha ma'lumotlar)
# - Form data (to'ldirilayotgan ma'lumotlar)
storage = RedisStorage(redis=redis)

# Dispatcher - barcha message'larni routing qiladi
dp = Dispatcher(storage=storage)


# ============================================================================
# STARTUP & SHUTDOWN HANDLERS
# ============================================================================

async def on_startup():
    """
    Application startup handler.

    Bu function FastAPI server ishga tushganda chaqiriladi.

    Vazifalar:
    ---------
    1. Barcha handler'larni register qilish
    2. Redis connection tekshirish
    3. Reminders scheduler'ni ishga tushirish (YANGI!)
    4. Logging
    """
    # Barcha handler'larni dispatcher'ga ulash
    # (start, passport, menu, contract, payments, reminders)
    register_all_handlers(dp)

    # Redis connection tekshirish
    try:
        await redis.ping()
        logger.success("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning("⚠️ Bot ishlamaydi! Redis'ni ishga tushiring:")
        logger.warning("   sudo systemctl start redis")
        raise

    # ✅ YANGI: Reminders scheduler'ni ishga tushirish
    try:
        from app.services.reminders import start_reminders_scheduler
        await start_reminders_scheduler(bot)
        logger.success("✅ Reminders scheduler started!")
    except Exception as e:
        logger.error(f"❌ Reminders scheduler failed: {e}")
        logger.warning("⚠️ Reminders ishlamaydi, lekin bot davom etadi")
        # Don't raise - bot should work even if reminders fail

    # ✅ YANGI: Support contact'ni yuklash (ERPNext'dan operator telefon raqami)
    try:
        from app.services.support import load_support_contact
        result = await load_support_contact()
        if result.get("success"):
            contact = result["contact"]
            logger.success(f"✅ Support contact loaded: {contact.get('name')} - {contact.get('phone')}")
        else:
            logger.warning("⚠️ Support contact not loaded, using config fallback")
    except Exception as e:
        logger.error(f"❌ Support contact loading failed: {e}")
        logger.warning("⚠️ Using config fallback for support contact")
        # Don't raise - bot should work even if support contact fails

    # Git commit hash'ni olish
    try:
        import subprocess
        git_commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd='/home/user/Documents/erpnext_bot'
        ).decode('utf-8').strip()
        git_branch = subprocess.check_output(
            ['git', 'branch', '--show-current'],
            cwd='/home/user/Documents/erpnext_bot'
        ).decode('utf-8').strip()
    except Exception:
        git_commit = "unknown"
        git_branch = "unknown"

    logger.success("🚀 Webhook bot ishga tushdi!")
    logger.info(f"📡 ERPNext Base URL: {config.erp.base_url}")
    logger.info(f"💾 Redis: {config.redis.host}:{config.redis.port}/{config.redis.db}")
    logger.info(f"🏷️  Version: {git_branch}@{git_commit}")


async def on_shutdown():
    logger.warning("🛑 Bot to'xtatilmoqda...")

    # Redis connection yopish
    try:
        await redis.close()
        logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.error(f"❌ Redis close error: {e}")

    # Bot session yopish
    try:
        await bot.session.close()
        logger.info("✅ Bot session closed")
    except Exception as e:
        logger.error(f"❌ Bot session close error: {e}")

    # ERPNext HTTP client yopish
    try:
        from app.services.erpnext_api import close_http_client
        await close_http_client()
    except Exception as e:
        logger.error(f"❌ HTTP client close error: {e}")

    logger.success("✅ Bot muvaffaqiyatli to'xtatildi")
