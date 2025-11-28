#!/usr/bin/env python3
"""
ERPNext Bot - Polling Mode
===========================

Simple polling mode deployment - no webhook, DNS, SSL needed!
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from app.config import config
from app.loader import bot, dp
from app.services.notification import notification_worker


async def main():
    """
    Start bot in polling mode with background notification worker.
    """
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("🚀 ERPNext Bot - Polling Mode")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"📋 Bot Token: {config.bot.token[:20]}...")
    logger.info(f"🔗 ERP URL: {config.erp.base_url}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Delete webhook (polling mode doesn't use it)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook deleted (polling mode)")

    # Start background notification worker
    asyncio.create_task(notification_worker())
    logger.info("✅ Background notification worker started")

    # Start polling
    logger.info("🔄 Starting polling...")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("⏹ Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        logger.exception("Full traceback:")
    finally:
        await bot.session.close()
        logger.info("👋 Bot session closed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹ Bot stopped")
