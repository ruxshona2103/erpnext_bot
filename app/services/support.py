"""
Support Service - Operator Kontaktlarini Boshqarish

Bu service ERPNext'dan operator telefon raqamini oladi va cache qiladi.
Xato xabarlarida dinamik operator telefon raqamini ko'rsatish uchun ishlatiladi.

Architecture:
-------------
1. Bot startup'da operator ma'lumotlarini yuklaydi
2. Redis'da cache qiladi (1 soat)
3. Xato xabarlarda cached ma'lumotlardan foydalanadi
4. Agar cache yo'q bo'lsa - ERPNext'dan qayta oladi

Cache Strategy:
---------------
- TTL: 3600 sekund (1 soat)
- Key: "support:contact"
- Automatic refresh: Bot startup va cache expire bo'lganda
"""

import json
from typing import Optional, Dict, Any
from loguru import logger

from app.services.erpnext_api import erp_get_support_contacts
from app.config import config


# ============================================================================
# GLOBAL CACHE (in-memory)
# ============================================================================

# In-memory cache - Redis'siz ham ishlaydi
_support_contact_cache: Optional[Dict[str, Any]] = None
_cache_timestamp: Optional[float] = None
CACHE_TTL = 3600  # 1 soat


# ============================================================================
# SUPPORT SERVICE FUNCTIONS
# ============================================================================

async def load_support_contact() -> Dict[str, Any]:
    """
    ERPNext'dan operator kontaktini yuklash va cache'lash.

    Bu funksiya bot startup'da chaqiriladi va operator ma'lumotlarini
    ERPNext'dan olib, in-memory cache'ga saqlaydi.

    Returns:
        {
            "success": True,
            "contact": {
                "name": "Operator",
                "phone": "+998 90 123 45 67"
            }
        }
    """
    global _support_contact_cache, _cache_timestamp

    try:
        logger.info("Loading support contact from ERPNext...")

        # ERPNext'dan olish
        data = await erp_get_support_contacts()

        if data.get("success") and data.get("contact"):
            contact = data["contact"]

            # Cache'ga saqlash
            _support_contact_cache = contact

            import time
            _cache_timestamp = time.time()

            logger.success(
                f"✅ Support contact loaded: {contact.get('name')} - {contact.get('phone')}"
            )

            return {
                "success": True,
                "contact": contact
            }
        else:
            logger.warning(
                f"⚠️ Support contact not found in ERPNext. "
                f"Using fallback from config."
            )

            # Fallback - config'dan olish
            fallback_contact = {
                "name": config.support.operator_name,
                "phone": config.support.phone,
                "source": "config_fallback"
            }

            _support_contact_cache = fallback_contact

            import time
            _cache_timestamp = time.time()

            return {
                "success": True,
                "contact": fallback_contact
            }

    except Exception as e:
        logger.error(f"Error loading support contact: {e}")
        logger.exception("Full traceback:")

        # Fallback - config'dan olish
        fallback_contact = {
            "name": config.support.operator_name,
            "phone": config.support.phone,
            "source": "config_fallback"
        }

        _support_contact_cache = fallback_contact

        return {
            "success": False,
            "contact": fallback_contact,
            "error": str(e)
        }


async def get_support_contact() -> Dict[str, str]:
    """
    Operator kontaktini olish (cache'dan yoki ERPNext'dan).

    Bu funksiya xato xabarlarda ishlatiladi.

    Flow:
    -----
    1. Agar cache mavjud va fresh bo'lsa - cache'dan qaytaradi
    2. Agar cache expire bo'lgan bo'lsa - ERPNext'dan qayta yuklaydi
    3. Agar ERPNext'dan olishda xato bo'lsa - config'dagi fallback'ni qaytaradi

    Returns:
        {
            "name": "Operator Ismi",
            "phone": "+998 90 123 45 67"
        }

    Example:
        >>> contact = await get_support_contact()
        >>> print(f"📞 {contact['name']}: {contact['phone']}")
    """
    global _support_contact_cache, _cache_timestamp

    # 1. Cache'ni tekshirish
    if _support_contact_cache and _cache_timestamp:
        import time
        cache_age = time.time() - _cache_timestamp

        # Cache fresh bo'lsa - qaytarish
        if cache_age < CACHE_TTL:
            logger.debug(f"Support contact from cache (age: {int(cache_age)}s)")
            return _support_contact_cache

        logger.info(f"Cache expired (age: {int(cache_age)}s). Refreshing...")

    # 2. Cache yo'q yoki expire bo'lgan - qayta yuklash
    result = await load_support_contact()

    if result.get("success"):
        return result["contact"]

    # 3. Fallback
    logger.warning("Using fallback support contact from config")
    return {
        "name": config.support.operator_name,
        "phone": config.support.phone
    }


def get_support_contact_sync() -> Dict[str, str]:
    """
    Operator kontaktini olish (sinxron versiya).

    Bu funksiya cache'dan o'qiydi va agar cache bo'lmasa - config'dan oladi.
    Async context'dan tashqarida ishlatish uchun.

    ⚠️ MUHIM: Bu funksiya faqat cache'dan o'qiydi, ERPNext'ga murojaat qilmaydi!

    Returns:
        {
            "name": "Operator",
            "phone": "+998 90 123 45 67"
        }
    """
    global _support_contact_cache

    if _support_contact_cache:
        return _support_contact_cache

    # Fallback - config'dan
    return {
        "name": config.support.operator_name,
        "phone": config.support.phone
    }


async def refresh_support_contact() -> bool:
    """
    Support contact cache'ni yangilash.

    Bu funksiya admin tomonidan qo'lda chaqirilishi mumkin
    (masalan, operator raqami o'zgarganda).

    Returns:
        bool: True - yangilandi, False - xato
    """
    logger.info("Manually refreshing support contact cache...")

    result = await load_support_contact()

    if result.get("success"):
        logger.success("✅ Support contact cache refreshed")
        return True

    logger.error("❌ Failed to refresh support contact cache")
    return False


def format_support_message(prefix: str = "Agar muammo davom etsa") -> str:
    """
    Support xabarini formatlash.

    Bu funksiya xato xabarlarda ishlatiladi.

    Args:
        prefix: Xabar boshlanishi

    Returns:
        Formatlangan support xabari

    Example:
        >>> msg = format_support_message()
        >>> print(msg)
        Agar muammo davom etsa, Operator'ga murojaat qiling:
        📞 +998 90 123 45 67
    """
    contact = get_support_contact_sync()

    return (
        f"{prefix}, {contact['name']}'ga murojaat qiling:\n"
        f"📞 {contact['phone']}"
    )


# ============================================================================
# ADMIN FUNCTIONS (optional)
# ============================================================================

async def test_support_api() -> Dict[str, Any]:
    """
    Support API'ni test qilish.

    Returns:
        {
            "success": True,
            "contact": {...},
            "cache_status": "fresh"
        }
    """
    # 1. Cache'ni tekshirish
    cache_contact = get_support_contact_sync()

    # 2. ERPNext'dan yangi ma'lumot olish
    api_result = await erp_get_support_contacts()

    # 3. Cache'ni refresh qilish
    await refresh_support_contact()

    return {
        "success": True,
        "cached_contact": cache_contact,
        "api_result": api_result,
        "message": "Support API test completed"
    }
