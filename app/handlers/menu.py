from aiogram import Router, F
from aiogram.types import Message

from app.utils.keyboard import main_menu_keyboard
from app.services.erpnext_api import erp_get_contracts_by_telegram_id

router = Router()


# ============================================================
# 1) ASOSIY MENYU — Mijozga info qaytarish
# ============================================================
async def menu_entry(msg: Message):
    """
    Foydalanuvchi asosiy menyuga qaytganda / menu tugmasini bosganda
    shunchaki asosiy menyuni ko'rsatamiz.
    """
    await msg.answer(
        "🟦 Asosiy menyuga qaytdingiz.\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=main_menu_keyboard()
    )


# ============================================================
# 2) MENYU → Shartnomalar
# ============================================================
async def menu_contracts(msg: Message):
    """
    🧾 Shartnomalar tugmasini bosganda
    Telegram ID bo'yicha ERPNext'dan shartnomalar chiqaramiz.
    """
    telegram_id = msg.from_user.id

    await msg.answer("🔎 Shartnomalar yuklanmoqda...")

    data = await erp_get_contracts_by_telegram_id(telegram_id)

    if not data or not data.get("success"):
        await msg.answer(
            "❌ Sizning Telegram hisobingiz ERPNext mijoziga bog‘lanmagan.\n\n"
            "Agar shartnomalar bo'lsa, passport orqali ulanishni amalga oshiring."
        )
        return

    contracts = data.get("contracts", [])

    if not contracts:
        await msg.answer(
            "📄 Sizga tegishli shartnomalar topilmadi.",
            reply_markup=main_menu_keyboard()
        )
        return

    # Keyin contract handler tugmalarini chaqiramiz
    from app.utils.keyboard import contract_list_keyboard
    kb = contract_list_keyboard(contracts)

    await msg.answer(
        f"📄 Sizda <b>{len(contracts)}</b> ta shartnoma mavjud.\n"
        f"Quyidan birini tanlang:",
        reply_markup=kb
    )


# ============================================================
# 3) MENYU → To‘lov tarixi
# ============================================================
async def menu_payments(msg: Message):
    """
    💳 To'lov tarixi bo‘limi
    """
    await msg.answer(
        "💳 To‘lov tarixini ko‘rish uchun shartnomani tanlang.\n\n"
        "Buning uchun:\n"
        "🧾 Shartnomalar → kerakli shartnomani tanlang → 💳 To‘lov tarixi",
        reply_markup=main_menu_keyboard()
    )


# ============================================================
# 4) MENYU → Mening profilim
# ============================================================
async def menu_profile(msg: Message):
    """
    👤 Profil — mijozning umumiy ma'lumotlari ERPNext'dan olinadi
    Telegram ID bo‘yicha.
    """
    telegram_id = msg.from_user.id

    await msg.answer("🔎 Profil ma'lumotlari yuklanmoqda...")

    data = await erp_get_contracts_by_telegram_id(telegram_id)

    if not data or not data.get("success"):
        await msg.answer(
            "❌ Profil topilmadi.\n"
            "Avval passport orqali ro‘yxatdan o‘ting."
        )
        return

    customer = data.get("customer")

    text = (
        f"👤 <b>{customer.get('name')}</b>\n"
        f"🆔 ID: <code>{customer.get('id')}</code>\n"
        f"📞 Telefon: <code>{customer.get('phone')}</code>\n"
        f"📲 Telegram ID: <code>{customer.get('telegram_id')}</code>\n"
        f"🏷 Klassifikatsiya: <code>{customer.get('classification')}</code>\n"
    )

    await msg.answer(text, reply_markup=main_menu_keyboard())


# ============================================================
# 5) ROUTER REGISTRATSIYA
# ============================================================
def register_menu_handlers(dp):
    dp.include_router(router)

    router.message.register(menu_entry, F.text == "⬅️ Orqaga")
    router.message.register(menu_contracts, F.text == "🧾 Shartnomalar")
    router.message.register(menu_payments, F.text == "💳 To'lov tarixi")
    router.message.register(menu_profile, F.text == "👤 Mening profilim")
