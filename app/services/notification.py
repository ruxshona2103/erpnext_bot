# app/services/notifications.py

import asyncio
from datetime import datetime, timedelta

from loguru import logger
from app.loader import bot
from app.services.erpnext_api import http_client


async def fetch_due_payments():
    """
    ERPNext dan kontraktlar va next_payment_date olish.
    """
    try:
        response = await http_client.get(
            "/api/resource/Sales Order",
            params={
                "fields": '["name","customer","custom_telegram_id","next_payment_date","next_payment_amount","customer_name"]',
                "limit_page_length": 500
            }
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception as e:
        logger.error(f"❌ fetch_due_payments error: {e}")
        return []


async def notification_worker():
    """
    Background worker: har 1 soatda ishlaydi.
    """
    logger.info("🔔 Notification worker started...")

    while True:
        try:
            orders = await fetch_due_payments()
            today = datetime.today().date()

            for so in orders:
                chat_id = so.get("custom_telegram_id")
                next_date_str = so.get("next_payment_date")

                if not chat_id or not next_date_str:
                    continue

                next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()

                # === 3 KUN OLDIN ===
                if next_date == today + timedelta(days=3):
                    await bot.send_message(
                        chat_id,
                        f"📅 3 kundan keyin to'lov kuni!\n\n"
                        f"Shartnoma: <b>{so['name']}</b>\n"
                        f"To'lov summasi: <b>{so['next_payment_amount']:,}</b> so'm\n"
                        f"🕒 Iltimos o'z vaqtida to'lang."
                    )

                # === 1 KUN OLDIN ===
                elif next_date == today + timedelta(days=1):
                    await bot.send_message(
                        chat_id,
                        f"📅 Ertaga to'lov kuni!\n\n"
                        f"Shartnoma: <b>{so['name']}</b>\n"
                        f"Summa: <b>{so['next_payment_amount']:,}</b> so'm"
                    )

                # === BUGUN ===
                elif next_date == today:
                    await bot.send_message(
                        chat_id,
                        f"📅 Bugun to'lov kuni!\n\n"
                        f"Shartnoma: <b>{so['name']}</b>\n"
                        f"To'lovni amalga oshirishingizni so'raymiz."
                    )

                # === 1 KUN O'TIB KETGAN ===
                elif next_date == today - timedelta(days=1):
                    await bot.send_message(
                        chat_id,
                        f"⚠️ Kecha to'lov muddati o'tdi!\n\n"
                        f"Shartnoma: <b>{so['name']}</b>\n"
                        f"Iltimos zudlik bilan to'lang."
                    )

                # === 1 KUNDAN KO‘P O‘TGAN (severe overdue) ===
                elif next_date < today - timedelta(days=1):
                    await bot.send_message(
                        chat_id,
                        f"❌ To'lov muddati o'tib ketgan!\n\n"
                        f"Shartnoma: <b>{so['name']}</b>\n"
                        f"⚠️ Iltimos imkon qadar tezroq to'lovni amalga oshiring."
                    )

        except Exception as e:
            logger.error(f"❌ Notification error: {e}")

        await asyncio.sleep(3600)
