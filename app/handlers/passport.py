from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger
import re

from app.states.user_states import PassportState
from app.services.erpnext_api import erp_get_customer_by_passport
from app.utils.formatters import format_customer_profile
from app.utils.keyboard import main_menu_keyboard
from app.services.support import get_support_contact


router = Router()

# Passport format validation regex
# Uzbekistan passport: 2 harf + 7 raqam (masalan: AB1234567, AA1234567)
PASSPORT_REGEX = re.compile(r'^[A-Z]{2}\d{7}$', re.IGNORECASE)

# 🛑 MUHIM: Menyu tugmalari ro'yxati (Bularni passport deb o'ylamasligi uchun)
MENU_COMMANDS = [
    "💳 To'lovlar tarixi",
    "📄 Mening shartnomalarim",
    "hek=llllloooo",
    "📅 Eslatmalar",
    "📞 Yordam",
    "/start",
    "🔍 Passport orqali qidirish",
    "To'lovlar tarixi",
    "Mening shartnomalarim",
    "Eslatmalar",
    "Yordam"
]

# =========================================================================
# 1. "PASSPORT ORQALI QIDIRISH" TUGMASI UCHUN HANDLER
# =========================================================================
@router.message(F.text == "🔍 Passport orqali qidirish")
async def passport_search_button_handler(msg: Message, state: FSMContext):
    """
    "🔍 Passport orqali qidirish" tugmasi bosilganda.
    """
    await msg.answer(
        "🔍 <b>Passport bo'yicha qidirish</b>\n\n"
        "Passport seriya raqamini kiriting:\n\n"
        "Masalan: <code>AB1234567</code> yoki <code>AA7654321</code>",
        reply_markup=main_menu_keyboard()
    )

    # Passport kutish state'ga o'tish
    await state.set_state(PassportState.waiting_for_passport)


@router.message(
    PassportState.waiting_for_passport,  # Faqat shu stateda ishlaydi
    F.text,                              # Matn bo'lishi shart
    ~F.text.in_(MENU_COMMANDS),          # Menyu tugmasi bo'lmasligi shart
    F.text.len() <= 12                   # Juda uzun matn bo'lmasligi shart
)
async def passport_input_handler(msg: Message, state: FSMContext):
    """
    Passport ID input handler.
    """
    passport = msg.text.strip().upper()  # Katta harfga o'girish
    telegram_id = msg.from_user.id

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
    loading_msg = await msg.answer("⏳ Ma'lumotlaringiz tekshirilmoqda...")

    try:
        # 2. ERPNext API'ga murojaat
        logger.info(f"Authenticating passport {passport} for telegram_id {telegram_id}")

        data = await erp_get_customer_by_passport(
            passport=passport,
            telegram_chat_id=telegram_id
        )

        await loading_msg.delete()

        # Success tekshiruvi
        success = data.get("success")
        has_customer = data.get("customer") is not None and len(data.get("customer", {})) > 0
        if isinstance(success, str):
            success = success.lower() in ('true', '1', 'yes')

        is_success = bool(success) and has_customer

        if is_success:
            # ✅ SUCCESS
            customer = data.get("customer", {})
            customer_name = customer.get("customer_name", "Mijoz")
            customer_id = customer.get("customer_id")
            is_new_link = data.get("is_new_link", False)

            if is_new_link:
                welcome_text = (
                    f"✅ <b>Muvaffaqiyatli!</b>\n\n"
                    f"Sizning Telegram account'ingiz muvaffaqiyatli bog'landi.\n"
                )
            else:
                welcome_text = f"✅ <b>Xush kelibsiz, {customer_name}!</b>\n\n"

            profile_text = format_customer_profile(data)

            await msg.answer(
                welcome_text + profile_text,
                reply_markup=main_menu_keyboard()
            )

            # State tozalash va ma'lumot saqlash
            await state.clear()
            await state.update_data(
                customer_id=customer_id,
                customer_name=customer_name,
                telegram_id=telegram_id
            )

        else:
            # ❌ FAILED
            error_message = data.get("message_uz") or data.get("message") or "Mijoz topilmadi"
            support = await get_support_contact()

            await msg.answer(
                f"❌ <b>Xatolik</b>\n\n"
                f"{error_message}\n\n"
                f"Iltimos, passport ID'ni tekshirib, qaytadan kiriting.\n"
                f"📞 Yordam: {support['phone']}",
                reply_markup=main_menu_keyboard()
            )

    except Exception as e:
        logger.error(f"Passport error: {e}")
        await loading_msg.delete()
        support = await get_support_contact()
        await msg.answer(f"❌ Tizim xatosi. 📞 {support['phone']}")
        await state.clear()


def register_passport_handlers(dp):
    """
    Handlerlarni ro'yxatdan o'tkazish
    """
    dp.include_router(router)