"""
Menu Handler - Asosiy menyu

Bu handler asosiy menyu'ga qaytish tugmasini boshqaradi.

DIQQAT:
-------
Shartnomalar, To'lovlar tarixi, Eslatmalar handler'lari boshqa fayllarda:
- app/handlers/contract.py
- app/handlers/payments.py
- app/handlers/reminders_handler.py

Bu yerda faqat "Orqaga" tugmasi va profil handler'lari qoldirilgan.
"""

from aiogram import Router, F
from aiogram.types import Message

from app.utils.keyboard import main_menu_keyboard
from app.services.erpnext_api import erp_get_contracts_by_telegram_id

router = Router()


# ============================================================
# 1) ASOSIY MENYU — Orqaga qaytish
# ============================================================
async def menu_entry(msg: Message):
    """
    Foydalanuvchi asosiy menyuga qaytganda.

    Bu handler "⬅️ Orqaga" tugmasi bosilganda ishga tushadi.
    """
    await msg.answer(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=main_menu_keyboard()
    )


# ============================================================
# 2) MENYU → Mening profilim
# ============================================================
async def menu_profile(msg: Message):
    """
    👤 Profil — mijozning umumiy ma'lumotlari ERPNext'dan olinadi
    Telegram ID bo'yicha.

    YANGI: format_customer_profile ishlatiladi - professional ko'rinish
    """
    telegram_id = msg.from_user.id

    await msg.answer("🔎 Profil ma'lumotlari yuklanmoqda...")

    data = await erp_get_contracts_by_telegram_id(telegram_id)

    if not data or not data.get("success"):
        await msg.answer(
            "❌ Profil topilmadi.\n\n"
            "Avval passport orqali ro'yxatdan o'ting.\n"
            "Buning uchun /start bosing.",
            reply_markup=main_menu_keyboard()
        )
        return

    # ✅ YANGI: Formatter ishlatish - chiroyli ko'rinish
    from app.utils.formatters import format_customer_profile

    profile_text = format_customer_profile(data)

    await msg.answer(profile_text, reply_markup=main_menu_keyboard())


# ============================================================
# 3) YORDAM TUGMASI
# ============================================================
async def menu_help(msg: Message):
    """
    ❓ Yordam tugmasi - /help commandiga o'tkazadi

    Bu handler "❓ Yordam" tugmasi bosilganda /help commandini chaqiradi.
    """
    # /help commandini chaqirish uchun start modulidagi help_message funksiyasini ishlatamiz
    from app.handlers.start import help_message
    await help_message(msg)


# ============================================================
# 4) ROUTER REGISTRATSIYA
# ============================================================
def register_menu_handlers(dp):
    """
    Menu handler'larni register qilish.

    DIQQAT: Faqat "Orqaga", "Profil" va "Yordam" handler'lari.
    Shartnomalar, To'lovlar, Eslatmalar - boshqa fayllarda.
    """
    dp.include_router(router)

    router.message.register(menu_entry, F.text == "⬅️ Orqaga")
    router.message.register(menu_help, F.text == "❓ Yordam")
    # PROFIL handler'i hozircha yoqilmagan - keyboard'da yo'q
    # router.message.register(menu_profile, F.text == "👤 Mening profilim")
