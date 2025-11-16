# app/services/erpnext_api.py

import httpx
from loguru import logger

from app.config import config


# ERPNext bilan ishlash uchun alohida HTTP klient
# (loader.py dagi http_client bilan aralashib ketmasligi uchun)
http_client = httpx.AsyncClient(
    base_url=config.erp.base_url,
    headers={
        "Authorization": f"token {config.erp.api_key}:{config.erp.api_secret}"
    },
    timeout=15.0,
    follow_redirects=True,
)


async def erp_request(method: str, endpoint: str, params=None, data=None):
    try:
        res = await http_client.request(
            method=method,
            url=endpoint,
            params=params,
            json=data,
        )
        res.raise_for_status()
        return res.json()
    except httpx.HTTPStatusError as e:
        # ERPNext javobi 4xx/5xx bo'lsa
        logger.error(
            f"ERP ERROR: {e} "
            f"status={e.response.status_code} url={e.request.url}"
        )
        return {
            "success": False,
            "message": f"ERPNext xato qaytardi: {e.response.status_code}",
            "status": e.response.status_code,
            "raw": e.response.text,
        }
    except Exception as e:
        logger.error(f"ERP ERROR: {e}")
        return {
            "success": False,
            "message": "ERPNext bilan bog'lanishda xatolik yuz berdi.",
        }


# ============================ #
# 1) Passport orqali mijoz
# ============================ #
async def erp_get_customer_by_passport(passport: str):
    """
    Passport seriyasi bo'yicha mijoz ma'lumotlari
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_customer_by_passport",
        params={"passport_series": passport},
    )

# ============================ #
# 2) Telegram ID biriktirish
# ============================ #
async def erp_link_telegram(customer_id: str, tg_id: int | str, username: str | None):
    """
    Mijozga Telegram ID / username biriktirish.
    """
    return await erp_request(
        method="POST",
        endpoint="/api/method/cash_flow_management.api.telegram_bot_api.link_telegram",
        data={
            "customer_id": customer_id,
            "telegram_id": tg_id,
            "username": username,
        },
    )


# ============================ #
# 3) Telegram ID orqali shartnomalar
# ============================ #
async def erp_get_contracts_by_telegram_id(tg_id: int | str):
    """
    Telegram chat ID bo'yicha barcha shartnomalar.
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_management.api.telegram_bot_api.get_contracts_by_telegram_id",
        params={"telegram_id": tg_id},
    )


# ============================ #
# 4) Shartnoma detali
# ============================ #
async def erp_get_contract_details(contract_id: str):
    """
    Bitta shartnoma bo'yicha to'liq ma'lumot + grafik.
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_management.api.telegram_bot_api.get_contract_details",
        params={"contract_id": contract_id},
    )


# ============================ #
# 5) To‘lov tarixi
# ============================ #
async def erp_get_payment_history(customer_id: str):
    """
    Customer ID bo'yicha to'lovlar tarixi.
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_management.api.telegram_bot_api.get_payment_history",
        params={"customer_id": customer_id},
    )


# ============================ #
# 6) Customer ID bo‘yicha shartnomalar (alohida method)
# ============================ #
async def erp_get_contracts_by_customer(customer_id: str):
    """
    Customer ID bo'yicha shartnomalar ro'yxatini olish.
    (ERPNext'dagi telegram_bot.api.get_customer_contracts methodiga boradi)
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/telegram_bot.api.get_customer_contracts",
        params={"customer": customer_id},
    )
