"""
Payment Reminders Service - To'lov eslatmalari

Bu modul mijozlarga to'lov vaqtlari haqida avtomatik eslatmalar yuboradi.

LOGIKA:
-------
1. Har kuni 1 marta ishga tushadi (background task)
2. ERPNext'dan yaqin to'lovlar ro'yxatini oladi
3. Har bir mijozga telegram orqali eslatma yuboradi

ESLATMA JADVALI:
---------------
- 5 kun oldin: "5 kundan keyin to'lov kuni!"
- 3 kun oldin: "⚠️ 3 kundan keyin to'lov!"
- 1 kun oldin: "❗ Ertaga to'lov kuni!"
- Bugun: "⏰ BUGUN to'lov kuni!"
- 1 kun kechikdi: "❌ To'lov 1 kun kechikdi!"
- 3 kun kechikdi: "🚨 To'lov 3 kun kechikdi!"
- 7 kun kechikdi: "🔴 To'lov 7 kun kechikdi!"

Architecture:
-------------
- AsyncIO task - background'da ishlaydi
- APScheduler ishlatiladi - har kuni 09:00 da
- Error handling - agar xato bo'lsa ham to'xtamaydi
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
from aiogram import Bot

from app.services.erpnext_api import erp_get_customers_needing_reminders
from app.config import config


# ============================================================================
# REMINDER TEMPLATES
# ============================================================================

def get_reminder_template(reminder_type: str, payment_data: Dict[str, Any]) -> str:
    """
    Eslatma xabari shablonini olish.

    Args:
        reminder_type: Eslatma turi (5_days_before, 3_days_before, etc.)
        payment_data: To'lov ma'lumotlari

    Returns:
        Formatted message
    """
    contract_id = payment_data.get('contract_id', '—')
    amount = payment_data.get('payment_amount', 0)
    due_date = payment_data.get('due_date', '—')
    days_left = payment_data.get('days_left', 0)

    # Format money
    from app.utils.formatters import format_money
    amount_formatted = format_money(amount)

    templates = {
        "5_days_before": (
            f"📅 <b>To'lov eslatmasi</b>\n\n"
            f"Sizning to'lovingiz 5 kundan keyin!\n\n"
            f"🔖 Shartnoma: <code>{contract_id}</code>\n"
            f"📆 Sana: <b>{due_date}</b>\n"
            f"💰 Summa: <b>${amount_formatted}</b>\n\n"
            f"Iltimos, to'lovni vaqtida amalga oshiring."
        ),
        "3_days_before": (
            f"⚠️ <b>To'lov eslatmasi</b>\n\n"
            f"Sizning to'lovingiz <b>3 kundan keyin!</b>\n\n"
            f"🔖 Shartnoma: <code>{contract_id}</code>\n"
            f"📆 Sana: <b>{due_date}</b>\n"
            f"💰 Summa: <b>${amount_formatted}</b>\n\n"
            f"To'lovni tayyorlab qo'ying!"
        ),
        "1_day_before": (
            f"❗ <b>To'lov eslatmasi</b>\n\n"
            f"Sizning to'lovingiz <b>ERTAGA!</b>\n\n"
            f"🔖 Shartnoma: <code>{contract_id}</code>\n"
            f"📆 Sana: <b>{due_date}</b>\n"
            f"💰 Summa: <b>${amount_formatted}</b>\n\n"
            f"Iltimos, ertaga to'lovni amalga oshiring."
        ),
        "today": (
            f"⏰ <b>To'lov BUGUN!</b>\n\n"
            f"Sizning to'lovingiz <b>BUGUN!</b>\n\n"
            f"🔖 Shartnoma: <code>{contract_id}</code>\n"
            f"📆 Sana: <b>{due_date}</b>\n"
            f"💰 Summa: <b>${amount_formatted}</b>\n\n"
            f"Iltimos, bugun to'lovni amalga oshiring."
        ),
        "1_day_overdue": (
            f"❌ <b>To'lov kechikdi!</b>\n\n"
            f"Sizning to'lovingiz <b>1 kun kechikdi!</b>\n\n"
            f"🔖 Shartnoma: <code>{contract_id}</code>\n"
            f"📆 To'lov kuni edi: <b>{due_date}</b>\n"
            f"💰 Summa: <b>${amount_formatted}</b>\n\n"
            f"Iltimos, imkon qadar tezroq to'lovni amalga oshiring."
        ),
        "3_days_overdue": (
            f"🚨 <b>To'lov kechikdi!</b>\n\n"
            f"Sizning to'lovingiz <b>3 kun kechikdi!</b>\n\n"
            f"🔖 Shartnoma: <code>{contract_id}</code>\n"
            f"📆 To'lov kuni edi: <b>{due_date}</b>\n"
            f"💰 Summa: <b>${amount_formatted}</b>\n\n"
            f"⚠️ Iltimos, to'lovni ZUDLIK bilan amalga oshiring!\n"
            f"Aks holda qarz yig'iladi."
        ),
        "7_days_overdue": (
            f"🔴 <b>JIDDIY: To'lov kechikdi!</b>\n\n"
            f"Sizning to'lovingiz <b>7 kun kechikdi!</b>\n\n"
            f"🔖 Shartnoma: <code>{contract_id}</code>\n"
            f"📆 To'lov kuni edi: <b>{due_date}</b>\n"
            f"💰 Summa: <b>${amount_formatted}</b>\n\n"
            f"🚨 <b>DIQQAT!</b> To'lovni zudlik bilan amalga oshiring!\n"
            f"Aks holda shartnoma to'xtatilishi mumkin.\n\n"
            f"Iltimos, biz bilan bog'laning:\n"
            f"📞 Telefon: +998 XX XXX XX XX"
        ),
    }

    return templates.get(reminder_type, templates["today"])


# ============================================================================
# SEND REMINDER
# ============================================================================

async def send_reminder(
    bot: Bot,
    telegram_chat_id: str,
    reminder_type: str,
    payment_data: Dict[str, Any]
) -> bool:
    """
    Bitta mijozga eslatma yuborish.

    Args:
        bot: Telegram Bot instance
        telegram_chat_id: Telegram chat ID
        reminder_type: Eslatma turi
        payment_data: To'lov ma'lumotlari

    Returns:
        bool: True - muvaffaqiyatli, False - xato
    """
    try:
        message = get_reminder_template(reminder_type, payment_data)

        await bot.send_message(
            chat_id=int(telegram_chat_id),
            text=message,
            parse_mode="HTML"
        )

        logger.info(
            f"✅ Reminder sent: {telegram_chat_id} - {reminder_type} - "
            f"{payment_data.get('contract_id')}"
        )

        return True

    except Exception as e:
        logger.error(
            f"❌ Failed to send reminder to {telegram_chat_id}: {e}"
        )
        return False


# ============================================================================
# PROCESS REMINDERS
# ============================================================================

async def process_reminders(bot: Bot):
    """
    Barcha eslatmalarni yuborish.

    Bu function har kuni 1 marta ishga tushadi va barcha mijozlarga
    kerakli eslatmalarni yuboradi.

    Args:
        bot: Telegram Bot instance
    """
    logger.info("🔔 Starting reminders processing...")

    try:
        # ERPNext'dan eslatma kerak bo'lgan mijozlar ro'yxatini olish
        response = await erp_get_customers_needing_reminders()

        if not response or not response.get("success"):
            logger.warning("⚠️ No reminders data from ERPNext")
            return

        reminders = response.get("reminders", [])

        if not reminders:
            logger.info("ℹ️ No reminders to send today")
            return

        logger.info(f"📊 Found {len(reminders)} reminders to send")

        # Har bir eslatmani yuborish
        sent = 0
        failed = 0

        for reminder in reminders:
            telegram_chat_id = reminder.get("telegram_chat_id")
            reminder_type = reminder.get("reminder_type", "today")

            if not telegram_chat_id:
                logger.warning(f"⚠️ No telegram_chat_id for {reminder.get('customer_id')}")
                failed += 1
                continue

            # Eslatma yuborish
            success = await send_reminder(bot, telegram_chat_id, reminder_type, reminder)

            if success:
                sent += 1
            else:
                failed += 1

            # Rate limiting - 30 xabar/soniyadan ko'p yubormaslik
            await asyncio.sleep(0.033)  # ~30 msg/sec

        logger.success(
            f"✅ Reminders processing completed: {sent} sent, {failed} failed"
        )

    except Exception as e:
        logger.error(f"❌ Reminders processing error: {e}")
        logger.exception("Full traceback:")


# ============================================================================
# SCHEDULED TASK
# ============================================================================

async def start_reminders_scheduler(bot: Bot):
    """
    Eslatmalar scheduler'ni ishga tushirish.

    Har kuni 09:00 da process_reminders() ni ishga tushiradi.

    Args:
        bot: Telegram Bot instance
    """
    logger.info("🕐 Starting reminders scheduler...")

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()

        # Har kuni 09:00 da ishga tushirish
        scheduler.add_job(
            process_reminders,
            trigger=CronTrigger(hour=9, minute=0),
            args=[bot],
            id="daily_reminders",
            name="Daily Payment Reminders",
            replace_existing=True
        )

        # Test uchun - har daqiqada (production'da o'chirish kerak!)
        # scheduler.add_job(
        #     process_reminders,
        #     trigger=CronTrigger(minute="*"),
        #     args=[bot],
        #     id="test_reminders",
        #     name="Test Reminders (every minute)",
        #     replace_existing=True
        # )

        scheduler.start()

        logger.success("✅ Reminders scheduler started successfully!")

    except ImportError:
        logger.error(
            "❌ APScheduler not installed! Install with: pip install apscheduler"
        )
    except Exception as e:
        logger.error(f"❌ Failed to start reminders scheduler: {e}")
        logger.exception("Full traceback:")


# ============================================================================
# MANUAL TRIGGER (TESTING)
# ============================================================================

async def trigger_reminders_now(bot: Bot):
    """
    Eslatmalarni darhol yuborish (testing uchun).

    Production'da bu function admin command orqali chaqirilishi mumkin.

    Args:
        bot: Telegram Bot instance
    """
    logger.info("🔔 Manual reminders trigger...")
    await process_reminders(bot)
