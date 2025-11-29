import asyncio
from datetime import datetime, timedelta

from loguru import logger
from app.loader import bot
from app.services.erpnext_api import http_client

API_METHOD = "/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_all_active_due_payments"


async def fetch_due_payments():
    """
    ERPNext dan hisob-kitob qilingan tayyor qarzdorliklarni oladi.
    """
    try:
        # GET so'rov yuboramiz (parametrlar shart emas, server o'zi hisoblaydi)
        response = await http_client.get(API_METHOD)

        # Statusni tekshiramiz
        response.raise_for_status()

        # Server {"data": [...]} ko'rinishida qaytaradi
        result = response.json()

        # Agar result ichida 'message' bo'lsa (Frappe ba'zan shunday qaytaradi)
        if "message" in result:
            return result["message"].get("data", [])

        return result.get("data", [])

    except Exception as e:
        logger.error(f"❌ fetch_due_payments error: {e}")
        return []


async def notification_worker():
    """
    Background worker: har 1 soatda ishlaydi.
    """
    logger.info("🔔 Notification worker started...")

    # Dastlab biroz kutib turamiz (bot to'liq yuklanishi uchun)
    await asyncio.sleep(5)

    while True:
        try:
            logger.info("🔄 Checking for due payments...")
            orders = await fetch_due_payments()

            if not orders:
                logger.info("✅ No active due payments found or API empty.")

            today = datetime.today().date()

            for so in orders:
                try:
                    chat_id = so.get("custom_telegram_id")
                    next_date_str = so.get("next_payment_date")
                    amount = so.get("next_payment_amount", 0)
                    contract_name = so.get("name")

                    if not chat_id or not next_date_str:
                        continue

                    next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()

                    # === 3 KUN OLDIN ===
                    if next_date == today + timedelta(days=3):
                        await bot.send_message(
                            chat_id,
                            f"📅 <b>3 kundan keyin to'lov kuni!</b>\n\n"
                            f"📄 Shartnoma: <b>{contract_name}</b>\n"
                            f"💰 To'lov summasi: <b>${amount:,.2f}</b>\n"
                            f"🕒 Iltimos o'z vaqtida to'lang."
                        )

                    # === 1 KUN OLDIN ===
                    elif next_date == today + timedelta(days=1):
                        await bot.send_message(
                            chat_id,
                            f"📅 <b>Ertaga to'lov kuni!</b>\n\n"
                            f"📄 Shartnoma: <b>{contract_name}</b>\n"
                            f"💰 Summa: <b>${amount:,.2f}</b>"
                        )

                    # === BUGUN ===
                    elif next_date == today:
                        await bot.send_message(
                            chat_id,
                            f"🔴 <b>DIQQAT: Bugun to'lov kuni!</b>\n\n"
                            f"📄 Shartnoma: <b>{contract_name}</b>\n"
                            f"💰 Summa: <b>${amount:,.2f}</b>\n\n"
                            f"Iltimos to'lovni amalga oshiring."
                        )

                    # === 1 KUN O'TIB KETGAN ===
                    elif next_date == today - timedelta(days=1):
                        await bot.send_message(
                            chat_id,
                            f"⚠️ <b>Kecha to'lov muddati o'tdi!</b>\n\n"
                            f"📄 Shartnoma: <b>{contract_name}</b>\n"
                            f"Iltimos zudlik bilan to'lang."
                        )

                    # === 3 KUN O'TIB KETGAN ===
                    elif next_date == today - timedelta(days=3):
                        await bot.send_message(
                            chat_id,
                            f"❌ <b>To'lov muddati o'tib ketgan!</b>\n\n"
                            f"📄 Shartnoma: <b>{contract_name}</b>\n"
                            f"⚠️ Sizda qarzdorlik mavjud. Iltimos, to'lov qiling!"
                        )

                except Exception as send_err:
                    logger.error(f"⚠️ Error sending message to {so.get('custom_telegram_id')}: {send_err}")

        except Exception as e:
            logger.error(f"❌ Notification worker error: {e}")

        # Har 1 soatda (3600 sekund) tekshiradi
        await asyncio.sleep(3600)