import asyncio
import sys
import logging
from pathlib import Path

# 1. Loyiha papkasini yo'lga qo'shish
sys.path.insert(0, str(Path(__file__).parent))

from app.loader import bot, dp
from app.handlers import register_all_handlers

# ----------------------------------------------------

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Bot ishga tushganda bajariladigan ishlar"""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🚀 Bot Polling Rejimida ishga tushmoqda")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 1. HANDLERLARNI RO'YXATDAN O'TKAZISH
    # Sizdagi register_all_handlers funksiyasi hamma "start", "menu"larni ulaydi
    try:
        register_all_handlers(dp)
        logger.info("✅ Barcha Handlerlar (register_all_handlers) muvaffaqiyatli ulandi!")
    except Exception as e:
        logger.error(f"❌ Handlerlarni ulashda xatolik: {e}")
        # Dasturni to'xtatamiz, chunki handlersiz bot ishlolmaydi
        sys.exit(1)

    # 2. Webhookni majburan o'chiramiz
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook o'chirildi")
    #
    # # 3. Notification (Eslatmalar) tizimini yoqamiz
    # asyncio.create_task(notification_worker())
    # logger.info("✅ Notification worker ishga tushdi")


async def main():
    # Startup funksiyasini chaqiramiz
    await on_startup()

    logger.info("🔄 Bot xabarlarni kutmoqda... (To'xtatish uchun Ctrl+C)")
    try:
        # Pollingni boshlaymiz
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Kutilmagan xatolik: {e}")
    finally:
        await bot.session.close()
        logger.info("👋 Bot sessiyasi yopildi")


if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot foydalanuvchi tomonidan to'xtatildi")