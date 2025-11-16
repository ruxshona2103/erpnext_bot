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


@router.post("/webhook/payment-entry")
async def payment_entry_webhook(request: Request):
    """
    ERPNext Payment Entry submit bo'lganda shu webhookga POST yuboradi.
    """
    data = await request.json()

    # ERPNext webhook JSON tarkibi
    pe_name = data.get("name")
    customer = data.get("party")
    contract = data.get("custom_contract_reference")
    amount = data.get("paid_amount")
    telegram_id = data.get("custom_telegram_id")

    if not telegram_id:
        return {"error": "Customer has no telegram_id"}

    msg = (
        f"💰 <b>To‘lov qabul qilindi!</b>\n\n"
        f"📄 Shartnoma: <b>{contract}</b>\n"
        f"💵 Summa: <b>{amount:,}</b> so‘m\n"
        f"🧾 To'lov ID: <b>{pe_name}</b>\n\n"
        f"Rahmat! 🙏"
    )

    await bot.send_message(chat_id=telegram_id, text=msg)

    return {"status": "ok"}
