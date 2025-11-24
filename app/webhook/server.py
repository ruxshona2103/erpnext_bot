from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from loguru import logger

from app.loader import bot, dp, on_startup, on_shutdown
from app.config import config

app = FastAPI(
    title="ERPNext Telegram Bot",
    docs_url=None,
    redoc_url=None
)

router = APIRouter()

# ✅ MUHIM: Router'ni app ga qo'shish - bu yo'q edi!
# Bu qator yo'qligi sababli /webhook/payment-entry ishlamagan!
app.include_router(router)


#Healthcheck (Cloudflare / UptimeRobot uchun)
@app.get("/")
async def root():
    return {"status": "ok", "message": "Webhook server is running"}

@app.post(config.telegram.webhook_path)
async def telegram_webhook(requests: Request):
    try:
        update_data = await  requests.json()
        await dp.feed_webhook_update(bot, update_data)
    except Exception as e :
        logger.error(f"Webhookda xatolik {e}")
        return JSONResponse(status_code=500, content={"ok": False})
    return JSONResponse(status_code=200, content={"ok": True})



# Server startup event
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI webhook server ishga tushdi")

    await on_startup()

    webhook_url = config.telegram.webhook_url + config.telegram.webhook_path

    # eski webhookni tozalaymiz
    await bot.delete_webhook(drop_pending_updates=True)

    # yangi webhookni o‘rnatamiz
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types()
    )

    logger.success(f"Webhook set: {webhook_url}")


# Server shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.warning("FastApi webhook toxtatilyapti...")
    await bot.delete_webhook(drop_pending_updates=True)
    await on_shutdown()
    logger.success("Webhook ochirildi, muvaffaqiyatli toxtatildi!")


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

        # ✅ Debug: Kelgan ma'lumotlarni log qilish
        logger.info(f"📥 Payment webhook received: {data}")

        # ERPNext webhook JSON tarkibi
        pe_name = data.get("name", "—")
        customer = data.get("party", "—")
        contract = data.get("custom_contract_reference", "—")
        amount = data.get("paid_amount", 0)
        telegram_id = data.get("custom_telegram_id")
        posting_date = data.get("posting_date", "")
        payment_method = data.get("mode_of_payment", "Naqd")

        # ✅ Telegram ID tekshirish
        if not telegram_id:
            logger.warning(f"⚠️ Payment {pe_name}: Customer {customer} has no telegram_id")
            return JSONResponse(
                status_code=200,
                content={"status": "skipped", "reason": "no_telegram_id"}
            )

        # ✅ Summa formatlash
        try:
            amount_formatted = f"{float(amount):,.0f}"
        except (ValueError, TypeError):
            amount_formatted = str(amount)

        # ✅ Xabar tayyorlash
        msg = (
            f"💰 <b>To'lov qabul qilindi!</b>\n\n"
            f"📄 Shartnoma: <code>{contract}</code>\n"
            f"💵 Summa: <b>{amount_formatted}</b> so'm\n"
            f"🏦 Usul: {payment_method}\n"
            f"🧾 To'lov ID: <code>{pe_name}</code>\n"
        )

        if posting_date:
            msg += f"📅 Sana: {posting_date}\n"

        msg += f"\n✅ Rahmat! Keyingi to'lovlar uchun /start bosing."

        # ✅ Telegram ga yuborish
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
