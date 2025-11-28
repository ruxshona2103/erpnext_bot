#!/usr/bin/env python3
"""
POLLING MODE - Simple and Reliable!
No webhook, DNS, SSL needed!
"""
import asyncio
import sys
from loguru import logger

sys.dont_write_bytecode = True

from app.loader import bot, dp, on_startup, on_shutdown


async def main():
    """Start bot in polling mode"""
    try:
        logger.info("🤖 Starting bot in POLLING mode...")
        logger.info("✅ No webhook/DNS/SSL needed!")

        # Startup
        await on_startup()

        # Delete any existing webhook
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.warning(f"⚠️ Removing old webhook: {webhook_info.url}")
            await bot.delete_webhook(drop_pending_updates=True)
            logger.success("✅ Webhook removed")

        logger.success("✅ Bot started successfully!")
        logger.info("📡 Polling for updates...")
        logger.info("💬 Send /start to your bot on Telegram")

        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )

    except KeyboardInterrupt:
        logger.warning("⚠️ Stopping bot (Ctrl+C)...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.exception("Full error:")
    finally:
        await on_shutdown()
        await bot.session.close()
        logger.success("👋 Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
