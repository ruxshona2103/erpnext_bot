"""
Start Handler - /start command

Bu handler bot'ning kirish nuqtasi - user birinchi marta yoki qaytadan /start bosaida.

Authentication Flow:
--------------------
1. User telegram_id ni ERPNext'dan tekshirish
2. Agar topilsa → Profil ma'lumotlarini ko'rsatish (avtomatik kirish)
3. Agar topilmasa → Passport ID so'rash (birinchi marta kirish)

ERPNext API:
------------
- get_customer_by_telegram_id(telegram_id) → Customer ma'lumotlari

Security:
---------
- Bitta telegram_id faqat bitta customer'ga tegishli
- ERPNext'da custom_telegram_id field'ida saqlanadi
- Passport bir marta kiritilgandan keyin, keyingi safar avtomatik
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.keyboard import main_menu_keyboard
from app.utils.formatters import format_customer_profile, format_error_message
from app.services.erpnext_api import erp_get_customer_by_telegram_id
from app.states.user_states import PassportState
from app.services.support import get_support_contact


router = Router()


async def start_message(msg: Message, state: FSMContext):
    """
    /start command handler.

    Flow:
    -----
    1. Telegram ID orqali ERPNext'da tekshirish
    2. Agar customer topilsa:
       - Profil va shartnomalarni ko'rsatish
       - Main menu ochish
    3. Agar customer topilmasa:
       - Passport ID so'rash
       - PassportState.waiting_for_passport state'ga o'tish

    Args:
        msg: Telegram message object
        state: FSM context (user state management)
    """
    user = msg.from_user
    telegram_id = user.id

    # Salomlashish
    await msg.answer(
        f"👋 Assalomu alaykum, <b>{user.full_name}</b>!\n\n"
        f"⏳ Ma'lumotlaringiz tekshirilmoqda...",
    )

    try:
        # ERPNext'dan telegram_id orqali customer topish
        logger.info(f"Checking telegram_id {telegram_id} in ERPNext...")
        data = await erp_get_customer_by_telegram_id(telegram_id)

        # ✅ SUCCESS CHECK - aniq va xavfsiz
        success = data.get("success")
        has_customer = data.get("customer") is not None and len(data.get("customer", {})) > 0

        # String "true" ham qabul qilish
        if isinstance(success, str):
            success = success.lower() in ('true', '1', 'yes')

        if bool(success) and has_customer:
            # ✅ Customer topildi - avtomatik kirish!
            customer = data.get("customer", {})
            customer_name = customer.get("customer_name", "Mijoz")

            logger.success(f"Customer found: {customer.get('customer_id')} - {customer_name}")

            # Profil ma'lumotlarini formatlash va ko'rsatish
            profile_text = format_customer_profile(data)

            await msg.answer(
                f"✅ <b>Xush kelibsiz, {customer_name}!</b>\n\n"
                f"{profile_text}",
                reply_markup=main_menu_keyboard()
            )

            # State tozalash (agar oldingi state qolgan bo'lsa)
            await state.clear()

            # Customer ID ni state'ga saqlash (keyingi handler'lar uchun)
            await state.update_data(
                customer_id=customer.get("customer_id"),
                customer_name=customer_name,
                telegram_id=telegram_id
            )

        else:
            # ❌ Customer topilmadi - birinchi marta kirish
            logger.info(f"Telegram ID {telegram_id} not found in ERPNext - requesting passport")

            await msg.answer(
                "📋 <b>Birinchi marta kirishingiz uchun passport ID ni kiriting</b>\n\n"
                "Masalan: <code>AB1234567</code> yoki <code>AA1234567</code>\n\n"
                "⚠️ Passport ID ni to'g'ri kiriting - bu sizning customer ma'lumotlaringizni topish uchun kerak.",
                reply_markup=main_menu_keyboard()
            )

            # Passport kutish state'ga o'tish
            await state.set_state(PassportState.waiting_for_passport)

    except Exception as e:
        # Xatolik yuz berdi
        logger.error(f"Start handler error: {e}")

        # Operator telefon raqamini olish
        support = await get_support_contact()

        await msg.answer(
            "❌ <b>Xatolik yuz berdi</b>\n\n"
            "ERPNext server bilan bog'lanib bo'lmadi. Iltimos, biroz kutib qaytadan urinib ko'ring.\n\n"
            f"Agar muammo davom etsa, {support['name']}'ga murojaat qiling:\n"
            f"📞 {support['phone']}",
            reply_markup=main_menu_keyboard()
        )

        # State tozalash
        await state.clear()


async def help_message(msg: Message):
    """
    /help command handler.

    Bot haqida ma'lumot va barcha mavjud commandlarni ko'rsatadi.
    Operator telefon raqamini ham ko'rsatadi.
    """
    user = msg.from_user

    help_text = (
        f"👋 <b>Assalomu alaykum, {user.full_name}!</b>\n\n"

        "🤖 <b>Bot haqida:</b>\n"
        "Ushbu bot orqali siz o'zingizning shartnomalaringiz, to'lovlar tarixi va "
        "eslatmalar bilan ishlashingiz mumkin.\n\n"

        "📋 <b>Asosiy bo'limlar:</b>\n"
        "• 📄 <b>Shartnomalar</b> - Barcha shartnomalaringizni ko'rish\n"
        "• 💳 <b>To'lovlar tarixi</b> - To'lovlaringiz tarixi\n"
        "• 🔔 <b>Eslatmalar</b> - Eslatmalarni boshqarish\n"
        "• ⬅️ <b>Orqaga</b> - Asosiy menyuga qaytish\n\n"

        "⌨️ <b>Commandlar:</b>\n"
        "/start - Botni ishga tushirish yoki qayta boshlash\n"
        "/help - Yordam va ko'rsatmalar (ushbu xabar)\n\n"

        "🔐 <b>Birinchi marta kirish:</b>\n"
        "Agar birinchi marta kirayotgan bo'lsangiz, /start commandini "
        "bosing va passport ID raqamingizni kiriting.\n\n"
    )

    # Operator telefon raqamini olish
    support = await get_support_contact()

    help_text += (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📞 <b>Operator bilan bog'lanish:</b>\n\n"
        f"👤 <b>Operator:</b> {support['name']}\n"
        f"📱 <b>Telefon:</b> <code>{support['phone']}</code>\n\n"
        "Agar biror savol yoki muammo bo'lsa, yuqoridagi raqamga qo'ng'iroq qiling.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    await msg.answer(help_text, reply_markup=main_menu_keyboard())


def register_start_handlers(dp):
    """
    Start handler'ni dispatcher'ga ulash.

    Args:
        dp: Dispatcher instance
    """
    dp.include_router(router)
    router.message.register(start_message, CommandStart())
    router.message.register(help_message, Command("help"))
