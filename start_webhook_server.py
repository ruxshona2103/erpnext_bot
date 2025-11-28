#!/usr/bin/env python3
"""
ERPNext webhooklari uchun alohida FastAPI server
Faqat ERPNext dan webhook qabul qilish uchun
Telegram webhooklari emas!
"""
import sys
sys.dont_write_bytecode = True

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.loader import bot
from app.config import config

# FastAPI app
app = FastAPI(
    title="ERPNext Webhook Server",
    description="ERPNext Payment Entry webhooklarini qabul qilish uchun",
    docs_url=None,
    redoc_url=None
)


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "message": "ERPNext Webhook Server is running",
        "endpoints": [
            "/webhook/payment-entry"
        ]
    }


@app.post("/webhook/payment-entry")
async def payment_entry_webhook(request: Request):
    """
    ERPNext Payment Entry submit bo'lganda shu webhookga POST yuboradi.

    ERPNext dan keladigan ma'lumotlar:
    - name: Payment Entry ID (PE-00001)
    - party: Customer ID
    - custom_contract_reference: Shartnoma ID
    - paid_amount: To'lov summasi
    - custom_telegram_id: Telegram chat ID
    - posting_date: To'lov sanasi (optional)
    - mode_of_payment: To'lov usuli (optional)
    """
    try:
        data = await request.json()

        # Debug: Kelgan ma'lumotlarni log qilish
        logger.info(f"📥 Payment webhook received: {data}")

        # ERPNext webhook JSON tarkibi
        pe_name = data.get("name", "—")
        customer = data.get("party", "—")
        contract = data.get("custom_contract_reference", "—")
        amount = data.get("paid_amount", 0)
        telegram_id = data.get("custom_telegram_id")
        posting_date = data.get("posting_date", "")
        payment_method = data.get("mode_of_payment", "Naqd")

        # Telegram ID tekshirish
        if not telegram_id:
            logger.warning(f"⚠️ Payment {pe_name}: Customer {customer} has no telegram_id")
            return JSONResponse(
                status_code=200,
                content={"status": "skipped", "reason": "no_telegram_id"}
            )

        # Summa formatlash
        try:
            amount_formatted = f"{float(amount):,.0f}"
        except (ValueError, TypeError):
            amount_formatted = str(amount)

        # Xabar tayyorlash
        msg = (
            f"💰 <b>To'lov qabul qilindi!</b>\n\n"
            f"📄 Shartnoma: <code>{contract}</code>\n"
            f"💵 Summa: <b>${amount_formatted}</b>\n"
            f"🧾 ID: <code>{pe_name}</code>\n"
        )

        if posting_date:
            msg += f"📅 Sana: {posting_date}\n"

        msg += f"\n✅ Rahmat! Keyingi to'lovlar uchun /start bosing."

        # Telegram ga yuborish
        await bot.send_message(
            chat_id=telegram_id,
            text=msg,
            parse_mode="HTML"
        )

        logger.success(f"✅ Payment notification sent to {telegram_id} for {pe_name}")

        return JSONResponse(
            status_code=200,
            content={"status": "ok", "telegram_id": telegram_id, "payment": pe_name}
        )

    except Exception as e:
        logger.error(f"❌ Payment webhook error: {e}")
        logger.exception("Full traceback:")

        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting ERPNext Webhook Server...")
    logger.info(f"📡 Port: 8002")
    logger.info(f"🔗 Webhook URL: http://your-server-ip:8002/webhook/payment-entry")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
