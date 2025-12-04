"""
Unknown Message Handler - Noma'lum xabarlarni ushlash

Bu handler foydalanuvchi tugma bosmay, oddiy matn yozib yuborsa ishga tushadi.
Foydalanuvchiga /start bosish yoki tugmalar orqali ishlash haqida yordam xabarini ko'rsatadi.

Handler Priority:
-----------------
Bu handler ENG OXIRIDA register qilinishi kerak, chunki u barcha noma'lum xabarlarni ushlaydi.
Agar birinchi bo'lsa, boshqa handler'lar ishlamay qoladi.

Security:
---------
- Faqat private chat'da ishlaydi
- Faqat text xabarlarga javob beradi
- Menu tugmalari uchun alohida handler bor
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.keyboard import main_menu_keyboard
from app.services.support import get_support_contact
from app.states.user_states import PassportState


router = Router()


@router.message(
    F.text,  # Faqat text xabarlari
    ~F.text.startswith("/"),  # Command emas
)
async def handle_unknown_message(msg: Message, state: FSMContext):
    """
    Noma'lum matn xabarlarini ushlash.

    Agar foydalanuvchi:
    - PassportState.waiting_for_passport state'da bo'lsa → passport.py handler ishleydi
    - Menu tugmasini bossa → menu.py handler ishleydi
    - Boshqa biror narsa yozsa → BU HANDLER ishleydi

    Flow:
    -----
    1. State'ni tekshirish (agar PassportState bo'lsa, o'tkazib yuborish)
    2. Foydalanuvchiga yordam xabarini ko'rsatish
    3. /start bosish yoki tugmalar orqali ishlashni tavsiya qilish

    Args:
        msg: Telegram message
        state: FSM context
    """
    user = msg.from_user
    current_state = await state.get_state()

    # Log qilish
    logger.warning(
        f"Unknown message from {user.id} ({user.full_name}): '{msg.text[:50]}...' "
        f"in state: {current_state or 'None'}"
    )

    # Agar foydalanuvchi passport kutish state'ida bo'lsa, passport handler'ga o'tkazish
    # Bu holat passport.py handler tomonidan handle qilinadi
    if current_state == PassportState.waiting_for_passport:
        # Passport handler ishleydi, bu yerda hech narsa qilmaslik kerak
        return

    # Operator telefon raqamini olish
    support = await get_support_contact()

    # Yordam xabarini yuborish
    help_text = (
        f"👋 <b>Salom, {user.full_name}!</b>\n\n"

        "❓ <b>Nimani qidiryapsiz?</b>\n\n"

        "🔹 Bot bilan ishlash uchun quyidagi <b>tugmalardan</b> foydalaning:\n\n"

        "📄 <b>Mening shartnomalarim</b> - Shartnomalaringizni ko'rish\n"
        "💳 <b>To'lovlar tarixi</b> - To'lovlar tarixini ko'rish\n"
        "📅 <b>Eslatmalar</b> - Eslatmalarni ko'rish\n"
        "❓ <b>Yordam</b> - Bot haqida to'liq ma'lumot\n"
        "👤 <b>Mening profilim</b> - Profilingizni ko'rish\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🔐 <b>Birinchi marta kiryapsizmi?</b>\n"
        "/start commandini bosing va passport ID raqamingizni kiriting.\n\n"

        "⌨️ <b>Foydali commandlar:</b>\n"
        "/start - Botni qayta boshlash\n"
        "/help - To'liq yordam\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "📞 <b>Yordam kerakmi?</b>\n"
        f"👤 Operator: <b>{support['name']}</b>\n"
        f"📱 Telefon: <code>{support['phone']}</code>\n\n"

        "💡 <b>Eslatma:</b> Iltimos, quyidagi tugmalar orqali ishlang. "
        "Oddiy matn yozish o'rniga tugmalardan foydalaning! 👇"
    )

    await msg.answer(help_text, reply_markup=main_menu_keyboard())


def register_unknown_handlers(dp):
    """
    Unknown handler'ni dispatcher'ga ulash.

    ⚠️ MUHIM: Bu handler ENG OXIRIDA register qilinishi kerak!

    Args:
        dp: Dispatcher instance
    """
    dp.include_router(router)
    logger.info("✅ Unknown message handler registered (LAST PRIORITY)")
