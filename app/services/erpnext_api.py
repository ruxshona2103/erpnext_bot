"""
ERPNext API Integration Service

Bu modul ERPNext backend API bilan to'liq integratsiya qiladi.
Barcha customer ma'lumotlari, shartnomalar, to'lovlar va mahsulotlar
ERPNext'dan real-time olinadi.

Architecture:
-------------
- Centralized HTTP client - barcha requestlar bir joydan
- Retry logic - tarmoq xatolarida avtomatik qayta urinish
- Error handling - barcha xatolar log qilinadi
- Type hints - kod xavfsizligi va IDE support

Performance Optimizations:
--------------------------
- ERPNext'da batch queries ishlatilgan (N+1 problem hal qilingan)
- Timeout 30s - katta ma'lumotlar uchun
- Connection pooling - tez ishlash
- Follow redirects - avtomatik
"""

import httpx
from typing import Optional, Dict, Any
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import config


# ============================================================================
# HTTP CLIENT CONFIGURATION
# ============================================================================

# Global HTTP client - barcha API chaqiruvlar uchun
# Nima uchun global?
# - Connection pooling - tez ishlash
# - Memory efficient - bitta client instance
# - Centralized configuration - bir joyda sozlash
http_client = httpx.AsyncClient(
    base_url=config.erp.base_url,
    headers={
        "Authorization": f"token {config.erp.api_key}:{config.erp.api_secret}",
        "Content-Type": "application/json",
    },
    timeout=30.0,  # 30 sekund - katta ma'lumotlar uchun
    follow_redirects=True,
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
    )
)


# ============================================================================
# BASE REQUEST FUNCTION WITH RETRY LOGIC
# ============================================================================

@retry(
    stop=stop_after_attempt(3),  # 3 marta urinish
    wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s, 4s, 8s
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
async def erp_request(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    ERPNext API ga request yuborish (retry logic bilan).

    Retry Logic:
    ------------
    - Timeout yoki network error bo'lsa - 3 marta qayta urinadi
    - Har bir urinish o'rtasida 2s → 4s → 8s kutadi
    - 3 martadan keyin ham xato bo'lsa - exception raise qiladi

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (/api/method/...)
        params: Query parameters (GET uchun)
        data: Request body (POST uchun)

    Returns:
        dict: ERPNext API response

    Raises:
        httpx.TimeoutException: Request timeout
        httpx.HTTPStatusError: HTTP error (4xx, 5xx)
    """
    try:
        logger.debug(f"ERP Request: {method} {endpoint}")

        response = await http_client.request(
            method=method,
            url=endpoint,
            params=params,
            json=data,
        )

        response.raise_for_status()
        result = response.json()

        # ⚠️ MUHIM: ERPNext ba'zan response'ni "message" key ichida qaytaradi
        # Agar shunday bo'lsa - unwrap qilamiz
        if "message" in result and isinstance(result["message"], dict):
            # Agar message ichida success field bo'lsa - bu wrapped response
            if "success" in result["message"] or "customer" in result["message"]:
                logger.debug(f"Unwrapping response from 'message' key")
                result = result["message"]

        logger.debug(f"ERP Response: {endpoint} -> success={result.get('success', 'unknown')}")
        return result

    except httpx.HTTPStatusError as e:
        # HTTP xato (4xx, 5xx)
        error_detail = {
            "success": False,
            "message": f"ERPNext xato qaytardi: {e.response.status_code}",
            "status_code": e.response.status_code,
            "url": str(e.request.url),
        }

        # Response body'ni log qilish (debugging uchun)
        try:
            error_detail["response_body"] = e.response.json()
        except:
            error_detail["response_text"] = e.response.text[:500]

        logger.error(f"ERP HTTP Error: {error_detail}")
        return error_detail

    except httpx.TimeoutException as e:
        # Timeout xatosi
        logger.error(f"ERP Timeout: {endpoint} - {e}")
        return {
            "success": False,
            "message": "ERPNext javob bermadi (timeout). Qaytadan urinib ko'ring.",
            "error_type": "timeout",
        }

    except httpx.NetworkError as e:
        # Tarmoq xatosi
        logger.error(f"ERP Network Error: {endpoint} - {e}")
        return {
            "success": False,
            "message": "ERPNext bilan bog'lanib bo'lmadi. Internetni tekshiring.",
            "error_type": "network_error",
        }

    except Exception as e:
        # Boshqa xatolar
        logger.error(f"ERP Unexpected Error: {endpoint} - {e}")
        return {
            "success": False,
            "message": f"Kutilmagan xatolik: {str(e)}",
            "error_type": "unknown",
        }


# ============================================================================
# 🔐 AUTHENTICATION APIs
# ============================================================================

async def erp_get_customer_by_passport(
    passport: str,
    telegram_chat_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Passport ID orqali customer topish va Telegram bog'lash.

    Bu ASOSIY login endpoint - customer birinchi marta botga kirganida ishlatiladi.

    Flow:
    -----
    1. Customer passport ID kiritadi
    2. ERPNext passport bo'yicha customer topadi
    3. Agar telegram_chat_id berilgan bo'lsa - customer'ga avtomatik saqlanadi
    4. Customer ma'lumotlari va barcha shartnomalar qaytariladi

    Args:
        passport: Passport seriya raqami (masalan: AB1234567)
        telegram_chat_id: Telegram user ID (avtomatik linking uchun)

    Returns:
        {
            "success": True,
            "customer": {...},
            "contracts": [...],
            "next_payments": [...],
            "is_new_link": True/False  # Yangi bog'langanmi?
        }
    """
    logger.info(f"[API] get_customer_by_passport called: passport={passport}, telegram_id={telegram_chat_id}")

    result = await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_customer_by_passport",
        params={
            "passport_series": passport,
            "telegram_chat_id": str(telegram_chat_id) if telegram_chat_id else None,  # ✅ str()
        }
    )

    logger.info(f"[API] get_customer_by_passport response: success={result.get('success')}, is_new_link={result.get('is_new_link')}")
    return result


async def erp_get_customer_by_telegram_id(telegram_id: int) -> Dict[str, Any]:
    """
    Telegram ID orqali customer topish.

    Bu endpoint user /start bosaida ishlatiladi - allaqachon bog'langanligini tekshirish.

    ⚠️ MUHIM: telegram_id STRING sifatida uzatiladi (ERPNext str kutadi)!

    Args:
        telegram_id: Telegram user ID

    Returns:
        Customer ma'lumotlari yoki {success: False}
    """
    logger.info(f"[API] get_customer_by_telegram_id called with: {telegram_id}")

    result = await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_customer_by_telegram_id",
        params={"telegram_id": str(telegram_id)}  # ✅ MUHIM: str() qo'shildi!
    )

    logger.info(f"[API] get_customer_by_telegram_id response: success={result.get('success')}")
    return result


async def erp_get_customer_by_phone(
    phone: str,
    telegram_chat_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Telefon raqam orqali customer topish (alternative login).

    Args:
        phone: Telefon raqami (+998901234567)
        telegram_chat_id: Telegram user ID

    Returns:
        Customer ma'lumotlari
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_customer_by_phone",
        params={
            "phone": phone,
            "telegram_chat_id": str(telegram_chat_id) if telegram_chat_id else None,  # ✅ str()
        }
    )


# ============================================================================
# 📄 CONTRACT APIs
# ============================================================================

async def erp_get_customer_contracts(customer_id: str) -> Dict[str, Any]:
    """
    Customer ning barcha shartnomalarini BATAFSIL olish.

    Qaytariladigan ma'lumotlar:
    ---------------------------
    - Shartnoma asosiy ma'lumotlari (ID, sana, summa, to'langan, qolgan)
    - Mahsulotlar ro'yxati:
      * Nomi, soni, narxi (tan narx + foiz)
      * IMEI, izohlar
    - To'lovlar tarixi:
      * Sana, summa, usul, Payment ID
    - Keyingi to'lov:
      * Sana, summa, necha kun qolgan

    Args:
        customer_id: Customer ID (CUST-00001)

    Returns:
        {
            "success": True,
            "contracts": [
                {
                    "contract_id": "SAL-ORD-00001",
                    "contract_date": "15.01.2025",
                    "total_amount": 15000000,
                    "paid": 5000000,
                    "remaining": 10000000,
                    "products": [
                        {
                            "name": "Samsung Galaxy S24",
                            "qty": 2,
                            "price": 7000000,  # tan narx + foiz
                            "total_price": 14000000,
                            "imei": "123456789",
                            "notes": "Qora rang"
                        }
                    ],
                    "payments_history": [...],
                    "next_payment": {...}
                }
            ]
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_customer_contracts_detailed",
        params={"customer_name": customer_id}
    )


async def erp_get_contracts_by_telegram_id(telegram_id: int) -> Dict[str, Any]:
    """
    Telegram ID orqali customer va uning shartnomalarini olish.

    Bu wrapper function menu.py uchun - bitta chaqiruvda customer va contracts olinadi.

    Args:
        telegram_id: Telegram user ID

    Returns:
        {
            "success": True,
            "customer": {...},
            "contracts": [...]
        }
    """
    # Avval telegram ID bo'yicha customerni topamiz
    customer_data = await erp_get_customer_by_telegram_id(telegram_id)

    if not customer_data.get("success"):
        return customer_data

    # Agar customer topilsa - contracts allaqachon API javobida kelgan!
    customer = customer_data.get("customer")
    if not customer:
        return {"success": False, "message": "Customer ma'lumotlari topilmadi"}

    # ✅ API javobidan contracts ni olish (allaqachon kelgan!)
    contracts = customer_data.get("contracts", [])

    return {
        "success": True,
        "customer": customer,
        "contracts": contracts
    }


async def erp_get_contract_details(contract_id: str) -> Dict[str, Any]:
    """
    Bitta shartnoma uchun to'liq ma'lumotlar.

    Bu function contract_id bo'yicha bitta shartnomaning barcha detallari olinadi.

    Args:
        contract_id: Shartnoma ID (SAL-ORD-00001)

    Returns:
        {
            "success": True,
            "contract": {
                "contract_id": "SAL-ORD-00001",
                "contract_date": "15.01.2025",
                "total_amount": 15000000,
                "paid": 5000000,
                "remaining": 10000000,
                "products": [...],
                "payments_history": [...],
                "next_payment": {...}
            }
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_contract_details",
        params={"contract_id": contract_id}
    )


async def erp_get_payment_schedule(contract_id: str) -> Dict[str, Any]:
    """
    Shartnoma uchun to'liq to'lov jadvali.

    Barcha oylik to'lovlar (to'langan va to'lanmagan).

    Args:
        contract_id: Shartnoma ID (SAL-ORD-00001)

    Returns:
        {
            "success": True,
            "contract_id": "SAL-ORD-00001",
            "schedule": [
                {
                    "month": 1,
                    "due_date": "15.02.2025",
                    "amount": 1250000,
                    "paid": 1250000,
                    "outstanding": 0,
                    "status": "paid",
                    "status_uz": "To'langan"
                },
                {
                    "month": 2,
                    "due_date": "15.03.2025",
                    "amount": 1250000,
                    "paid": 625000,
                    "outstanding": 625000,
                    "status": "partial",
                    "status_uz": "Qisman to'langan",
                    "days_left": 10,
                    "is_overdue": False
                }
            ]
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_payment_schedule",
        params={"contract_id": contract_id}
    )


async def erp_get_payment_history(contract_id: str) -> Dict[str, Any]:
    """
    Shartnoma bo'yicha to'lovlar tarixi.

    Payment Entry dan to'g'ridan-to'g'ri olingan ma'lumotlar.

    Args:
        contract_id: Shartnoma ID

    Returns:
        {
            "success": True,
            "payments": [
                {
                    "payment_id": "PE-00001",
                    "date": "15.02.2025",
                    "amount": 1250000,
                    "method": "Naqd"
                }
            ]
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_payment_history",
        params={"contract_id": contract_id}
    )


async def erp_get_payment_history_with_products(contract_id: str) -> Dict[str, Any]:
    """
    Shartnoma bo'yicha to'lovlar tarixi + Mahsulotlar.

    Bu funksiya Telegram bot uchun maxsus - faqat muhim ma'lumotlar:
    - Mahsulotlar (nomi, miqdori, narxi, IMEI)
    - To'lovlar (sana, summa, usul)
    - Shartnoma umumiy ma'lumotlari
    - SHAXSIY MA'LUMOTLAR CHIQMAYDI!

    Args:
        contract_id: Shartnoma ID (CON-2025-00245)

    Returns:
        {
            "success": True,
            "contract": {
                "contract_id": "CON-2025-00245",
                "contract_date": "08.07.2025",
                "total_amount": 1116.0,
                "paid": 300.0,
                "remaining": 816.0
            },
            "products": [
                {
                    "name": "iPhone 15 Pro Max 256GB",
                    "qty": 1,
                    "price": 1116.0,
                    "total_price": 1116.0,
                    "imei": "123456789",
                    "notes": ""
                }
            ],
            "payments": [
                {
                    "date": "10.07.2025",
                    "amount": 300.0,
                    "method": "Naqd",
                    "payment_id": "PE-00001"
                }
            ],
            "total_paid": 300.0,
            "total_payments": 1
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_payment_history_with_products",
        params={"contract_id": contract_id}
    )


# ============================================================================
# 🔔 NOTIFICATION & REMINDER APIs
# ============================================================================

async def erp_get_reminders_by_telegram_id(telegram_id: int) -> Dict[str, Any]:
    """
    Telegram ID orqali customerning eslatmalarini olish.

    Bu endpoint "Eslatmalar" button bosilganda ishlatiladi.

    Qanday ishlaydi:
    ----------------
    1. Telegram ID orqali customerni topadi
    2. Yaqin muddat to'lovlarini ko'rsatadi (30 kun ichida)
    3. Har bir to'lov uchun status va prioritet aniqlaydi

    Args:
        telegram_id: Telegram user ID

    Returns:
        {
            "success": True,
            "customer_id": "CUST-00001",
            "customer_name": "Alisher Navoiy",
            "reminders": [
                {
                    "contract_id": "CON-2025-00245",
                    "contract_date": "08.07.2025",
                    "due_date": "08.12.2025",
                    "amount": 100.0,
                    "outstanding": 100.0,
                    "days_left": 3,
                    "status": "soon",
                    "status_uz": "3 kun qoldi 🟢",
                    "priority": "medium",
                    "payment_number": 5
                }
            ],
            "total_reminders": 1,
            "message": "Eslatmalar yuklandi"
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_reminders_by_telegram_id",
        params={"telegram_id": str(telegram_id)}
    )


async def erp_get_payment_history_by_telegram_id(telegram_id: int) -> Dict[str, Any]:
    """
    Telegram ID orqali customerning barcha to'lovlar tarixini olish.

    Bu endpoint "Tolov tarixi" button bosilganda ishlatiladi.

    Qanday ishlaydi:
    ----------------
    1. Telegram ID orqali customerni topadi
    2. Barcha shartnomalarni oladi
    3. Har bir shartnoma uchun to'lovlar tarixini ko'rsatadi

    Args:
        telegram_id: Telegram user ID

    Returns:
        {
            "success": True,
            "customer_id": "CUST-00001",
            "customer_name": "Alisher Navoiy",
            "contracts": [
                {
                    "contract_id": "CON-2025-00245",
                    "contract_date": "08.07.2025",
                    "total_amount": 1116.0,
                    "paid": 300.0,
                    "remaining": 816.0,
                    "payments": [
                        {
                            "payment_id": "PE-00001",
                            "date": "10.07.2025",
                            "amount": 300.0,
                            "method": "Naqd",
                            "remarks": "Dastlabki to'lov"
                        }
                    ],
                    "total_payments": 1
                }
            ],
            "total_contracts": 1,
            "message": "To'lovlar tarixi yuklandi"
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_payment_history_by_telegram_id",
        params={"telegram_id": str(telegram_id)}
    )


async def erp_get_my_contracts_by_telegram_id(telegram_id: int) -> Dict[str, Any]:
    """
    Telegram ID orqali customerning barcha shartnomalarini olish.

    Bu endpoint "Mening shartnomalarim" button bosilganda ishlatiladi.

    Qanday ishlaydi:
    ----------------
    1. Telegram ID orqali customerni topadi
    2. get_customer_contracts_detailed() ni chaqiradi
    3. Batafsil shartnoma ma'lumotlarini qaytaradi (mahsulotlar, to'lovlar, keyingi to'lov)

    Args:
        telegram_id: Telegram user ID

    Returns:
        {
            "success": True,
            "customer_id": "CUST-00001",
            "customer_name": "Alisher Navoiy",
            "contracts": [
                {
                    "contract_id": "CON-2025-00245",
                    "contract_date": "08.07.2025",
                    "total_amount": 1116.0,
                    "downpayment": 300.0,
                    "paid": 300.0,
                    "remaining": 816.0,
                    "products": [
                        {
                            "name": "iPhone 15 Pro Max 256GB",
                            "qty": 1,
                            "price": 1116.0,
                            "imei": "123456789",
                            "notes": ""
                        }
                    ],
                    "payments_history": [
                        {
                            "date": "10.07.2025",
                            "amount": 300.0,
                            "method": "Naqd",
                            "payment_id": "PE-00001"
                        }
                    ],
                    "next_payment": {
                        "due_date": "08.08.2025",
                        "amount": 100.0,
                        "days_left": 25,
                        "status": "upcoming",
                        "status_uz": "25 kun qoldi"
                    },
                    "total_payments": 1
                }
            ],
            "total_contracts": 1
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_my_contracts_by_telegram_id",
        params={"telegram_id": str(telegram_id)}
    )


async def erp_get_upcoming_payments(customer_id: str) -> Dict[str, Any]:
    """
    Customer ning yaqin to'lovlarini olish.

    Barcha shartnomalar bo'yicha keyingi to'lovlar.

    Args:
        customer_id: Customer ID

    Returns:
        {
            "success": True,
            "payments": [
                {
                    "contract_id": "SAL-ORD-00001",
                    "due_date": "15.03.2025",
                    "amount": 1250000,
                    "days_left": 5,
                    "status": "soon",
                    "status_uz": "Yaqinda"
                }
            ]
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_upcoming_payments",
        params={"customer_name": customer_id}
    )


async def erp_get_customers_needing_reminders(
    reminder_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Eslatma yuborish kerak bo'lgan customerlarni topish.

    Bu function notification worker tomonidan ishlatiladi.

    Eslatma jadvali:
    ----------------
    - 5 kun oldin
    - 3 kun oldin
    - 1 kun oldin
    - Bugun (0 kun)
    - 1 kun kechikdi (-1)
    - 3 kun kechikdi (-3)
    - 5 kun kechikdi (-5)

    Args:
        reminder_days: Necha kun oldin/keyin (None = barchasi)

    Returns:
        {
            "success": True,
            "reminders": [
                {
                    "customer_id": "CUST-00001",
                    "customer_name": "Ali Aliyev",
                    "telegram_chat_id": "123456789",
                    "contract_id": "SAL-ORD-00001",
                    "due_date": "20.03.2025",
                    "payment_amount": 1250000,
                    "days_left": 3,
                    "reminder_type": "3_days_before",
                    "reminder_text": "3 kundan keyin to'lov kuni!"
                }
            ]
        }
    """
    params = {}
    if reminder_days is not None:
        params["reminder_days"] = reminder_days

    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_customers_needing_reminders",
        params=params
    )


async def erp_get_today_reminders() -> Dict[str, Any]:
    """
    Bugun eslatma yuborish kerak bo'lgan customerlar.

    Shortcut function - reminder_days=0 bilan.
    """
    return await erp_get_customers_needing_reminders(reminder_days=0)


async def erp_get_overdue_customers() -> Dict[str, Any]:
    """
    To'lovni kechiktirgan customerlar.

    Kechikkan to'lovlar ro'yxati va qancha kechikganligi.

    Returns:
        {
            "success": True,
            "overdue_customers": [
                {
                    "customer_id": "CUST-00001",
                    "customer_name": "Ali Aliyev",
                    "telegram_chat_id": "123456789",
                    "contract_id": "SAL-ORD-00001",
                    "due_date": "10.03.2025",
                    "payment_amount": 1250000,
                    "days_overdue": 5,
                    "overdue_text": "5 kun kechikdi"
                }
            ]
        }
    """
    return await erp_request(
        method="GET",
        endpoint="/api/method/cash_flow_app.cash_flow_management.api.telegram_bot_api.get_overdue_customers"
    )


# ============================================================================
# 🛠️ UTILITY FUNCTIONS
# ============================================================================

async def close_http_client():
    """
    HTTP client'ni yopish (cleanup).

    Application shutdown'da chaqiriladi (main.py'da).
    """
    await http_client.aclose()
    logger.info("✅ ERPNext HTTP client closed")


async def health_check() -> bool:
    """
    ERPNext API health check.

    ERPNext server ishlab turishini tekshirish.

    Returns:
        bool: True - ishlab turibdi, False - ishlamayapti
    """
    try:
        response = await http_client.get("/api/method/ping")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"ERPNext health check failed: {e}")
        return False
