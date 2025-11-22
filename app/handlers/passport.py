"""
Passport Handler - First-time Authentication

Bu handler birinchi marta botga kirgan foydalanuvchilar uchun.
Passport ID orqali customer topiladi va telegram_id avtomatik bog'lanadi.

Authentication Process:
-----------------------
1. User passport ID kiritadi (AB1234567)
2. Bot ERPNext API'ga murojaat qiladi (telegram_id bilan)
3. ERPNext:
   - Passport bo'yicha customer topadi
   - Telegram_id ni customer'ga saqlayyapti
   - To'liq ma'lumotlarni qaytaradi
4. Bot customer profilini ko'rsatadi

Security:
---------
- Bitta passport faqat bitta telegram_id bilan bog'lanishi mumkin
- ERPNext'da tekshiriladi va saqlanadi
- Keyingi safar passport so'ralmaydi (telegram_id bilan avtomatik)

ERPNext API:
------------
- erp_get_customer_by_passport(passport, telegram_chat_id)
  → Customer ma'lumotlari + avtomatik telegram_id linking
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger
import re

from app.states.user_states import PassportState
from app.services.erpnext_api import erp_get_customer_by_passport
from app.utils.formatters import format_customer_profile, format_error_message
from app.utils.keyboard import main_menu_keyboard


router = Router()


# Passport format validation regex
# Uzbekistan passport: 2 harf + 7 raqam (masalan: AB1234567, AA1234567)
PASSPORT_REGEX = re.compile(r'^[A-Z]{2}\d{7}$', re.IGNORECASE)


async def passport_search_button_handler(msg: Message, state: FSMContext):
    """
    "🔍 Passport orqali qidirish" tugmasi bosilganda.

    Bu tugma user allaqachon bog'langan bo'lsa ham, boshqa customer'ni
    qidirishi uchun yoki qayta passport kiritishi uchun.

    Flow:
    -----
    1. Passport kiritishni so'rash
    2. PassportState.waiting_for_passport state'ga o'tish
    3. passport_input_handler ishga tushadi
    """
    await msg.answer(
        "🔍 <b>Passport bo'yicha qidirish</b>\n\n"
        "Passport seriya raqamini kiriting:\n\n"
        "Masalan: <code>AB1234567</code> yoki <code>AA7654321</code>",
        reply_markup=main_menu_keyboard()
    )

    # Passport kutish state'ga o'tish
    await state.set_state(PassportState.waiting_for_passport)


async def passport_input_handler(msg: Message, state: FSMContext):
    """
    Passport ID input handler - birinchi marta authentication.

    Flow:
    -----
    1. Passport format tekshirish (AA1234567 formatda bo'lishi kerak)
    2. ERPNext API'ga murojaat qilish (passport + telegram_id)
    3. Agar customer topilsa:
       - Telegram_id avtomatik bog'lanadi (ERPNext tomonida)
       - Customer profili ko'rsatiladi
       - Main menu ochiladi
    4. Agar topilmasa:
       - Xato xabari
       - Qaytadan passport so'raladi

    Args:
        msg: Telegram message object
        state: FSM context
    """
    passport = msg.text.strip().upper()  # Katta harfga o'girish
    telegram_id = msg.from_user.id
    username = msg.from_user.username

    # 1. Passport format validation
    if not PASSPORT_REGEX.match(passport):
        await msg.answer(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "Passport ID 2 ta harf va 7 ta raqamdan iborat bo'lishi kerak.\n\n"
            "Masalan: <code>AB1234567</code> yoki <code>AA7654321</code>\n\n"
            "Iltimos, qaytadan kiriting:",
            reply_markup=main_menu_keyboard()
        )
        return

    # Loading message
    loading_msg = await msg.answer(
        "⏳ Ma'lumotlaringiz tekshirilmoqda...\n"
        "Iltimos, kuting..."
    )

    try:
        # 2. ERPNext API'ga murojaat - passport va telegram_id bilan
        logger.info(f"Authenticating passport {passport} for telegram_id {telegram_id}")

        data = await erp_get_customer_by_passport(
            passport=passport,
            telegram_chat_id=telegram_id  # Avtomatik linking uchun!
        )

        # DEBUG: API response'ni log qilish
        logger.debug(f"API Response keys: {list(data.keys())}")
        logger.debug(f"Success value: {data.get('success')}, Type: {type(data.get('success'))}")

        # Loading message o'chirish
        await loading_msg.delete()

        # ✅ SUCCESS CHECK - aniq va xavfsiz
        # success field tekshirish (True, "true", 1, etc.)
        success = data.get("success")
        has_customer = data.get("customer") is not None and len(data.get("customer", {})) > 0

        # String "true" yoki "True" ham qabul qilish (ERPNext ba'zan string qaytarishi mumkin)
        if isinstance(success, str):
            success = success.lower() in ('true', '1', 'yes')

        is_success = bool(success) and has_customer

        logger.debug(f"Is Success: {is_success} (success={success}, has_customer={has_customer})")

        if is_success:
            # ✅ SUCCESS - Customer topildi va bog'landi!
            logger.info("🟢 SUCCESS block entered!")

            customer = data.get("customer", {})
            customer_name = customer.get("customer_name", "Mijoz")
            customer_id = customer.get("customer_id")
            is_new_link = data.get("is_new_link", False)

            logger.success(
                f"Authentication successful: {customer_id} ({customer_name}) "
                f"linked to telegram_id {telegram_id} "
                f"(new_link: {is_new_link})"
            )

            # Xush kelibsiz xabari
            if is_new_link:
                welcome_text = (
                    f"✅ <b>Muvaffaqiyatli!</b>\n\n"
                    f"Sizning Telegram account'ingiz muvaffaqiyatli bog'landi.\n\n"
                    f"Keyingi safar passport kiritishingiz shart emas - "
                    f"avtomatik tanilasiz! 🎉\n\n"
                )
            else:
                welcome_text = (
                    f"✅ <b>Xush kelibsiz, {customer_name}!</b>\n\n"
                )

            # Customer profilini formatlash
            profile_text = format_customer_profile(data)

            await msg.answer(
                welcome_text + profile_text,
                reply_markup=main_menu_keyboard()
            )

            # State tozalash
            await state.clear()

            # Customer ma'lumotlarini state'ga saqlash (keyingi handler'lar uchun)
            await state.update_data(
                customer_id=customer_id,
                customer_name=customer_name,
                telegram_id=telegram_id,
                passport=passport
            )

        else:
            # ❌ FAILED - Customer topilmadi yoki xato
            logger.error("🔴 ELSE block entered! success=False or customer=None")
            logger.error(f"API success: {data.get('success')}, has customer: {bool(data.get('customer'))}")
            logger.debug(f"Full API response keys: {list(data.keys())}")

            # ⚠️ MUHIM: error_message ni xavfsiz olish
            error_message = data.get("message_uz") or data.get("message")

            # Agar error_message None yoki dict bo'lsa - default message
            if not error_message or not isinstance(error_message, str):
                error_message = "Passport ID bo'yicha mijoz topilmadi"

            logger.warning(f"Passport {passport} authentication failed: {error_message}")

            await msg.answer(
                f"❌ <b>Xatolik</b>\n\n"
                f"{error_message}\n\n"
                "Iltimos, passport ID'ni tekshirib, qaytadan kiriting.\n\n"
                "<i>Agar muammo davom etsa, administratorga murojaat qiling:</i>\n"
                "📞 Telefon: +998 XX XXX XX XX",
                reply_markup=main_menu_keyboard()
            )

            # State saqlanadi - qaytadan passport kutadi

    except Exception as e:
        # Xatolik yuz berdi
        logger.error("🔴 EXCEPTION block entered!")
        logger.error(f"Passport authentication error: {e}")
        logger.exception("Full traceback:")

        await loading_msg.delete()

        await msg.answer(
            "❌ <b>Tizim xatosi!</b>\n\n"
            "ERPNext server bilan bog'lanib bo'lmadi.\n\n"
            "Iltimos, biroz kutib qaytadan urinib ko'ring.\n\n"
            "Agar muammo davom etsa, administratorga xabar bering.",
            reply_markup=main_menu_keyboard()
        )

        # State tozalash - qaytadan /start bosishi kerak
        await state.clear()


def register_passport_handlers(dp):
    """
    Passport handler'ni dispatcher'ga ulash.

    Args:
        dp: Dispatcher instance
    """
    dp.include_router(router)

    # ✅ YANGI: "🔍 Passport orqali qidirish" tugmasi uchun handler
    router.message.register(
        passport_search_button_handler,
        F.text == "🔍 Passport orqali qidirish"
    )

    # Passport kutayotgan state'da text message kelsa - bu handler ishlaydi
    router.message.register(
        passport_input_handler,
        PassportState.waiting_for_passport,
        F.text  # Faqat text message'lar
    )
