"""
Reminders Handler - Eslatmalar

Bu handler "📅 Eslatmalar" tugmasi bosilganda ishga tushadi.

Vazifalar:
----------
1. Telegram ID orqali customerni topadi (passport so'ramaydi!)
2. Yaqin muddatdagi to'lovlarni ko'rsatadi (30 kun ichida)
3. Har bir to'lov uchun:
   - Status (bugun, ertaga, 3 kun qoldi, kechikkan)
   - Qoldiq summa
   - To'lov sanasi

Flow:
-----
User: "📅 Eslatmalar" tugmasini bosadi
Bot: Telegram ID orqali ERPNext'dan eslatmalarni oladi
Bot: Eslatmalarni chiroyli formatda ko'rsatadi
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.utils.keyboard import main_menu_keyboard
from app.utils.formatters import format_money
from app.services.erpnext_api import erp_get_reminders_by_telegram_id


router = Router()


async def show_reminders(msg: Message, state: FSMContext):
    """
    Eslatmalarni ko'rsatish.

    Bu function "📅 Eslatmalar" tugmasi bosilganda ishga tushadi.

    Args:
        msg: Telegram message object
        state: FSM context (kerak bo'lsa)
    """
    telegram_id = msg.from_user.id

    # Loading message
    await msg.answer("⏳ Eslatmalar yuklanmoqda...")

    try:
        # ERPNext'dan eslatmalarni olish
        logger.info(f"Fetching reminders for telegram_id: {telegram_id}")
        data = await erp_get_reminders_by_telegram_id(telegram_id)

        # Success check
        if not data or not data.get("success"):
            await msg.answer(
                "❌ <b>Sizning Telegram hisobingiz ERPNext mijoziga bog'lanmagan</b>\n\n"
                "Avval /start bosib, passport raqamingizni kiriting.\n\n"
                "Passport kiritgansiz, lekin bu xato chiqsa - admin bilan bog'laning.",
                reply_markup=main_menu_keyboard()
            )
            return

        # Eslatmalarni olish
        reminders = data.get("reminders", [])
        customer_name = data.get("customer_name", "Mijoz")

        # Agar eslatma yo'q bo'lsa
        if not reminders:
            await msg.answer(
                f"✅ <b>{customer_name}, sizda yaqin muddatda to'lov yo'q!</b>\n\n"
                f"Barcha to'lovlaringiz rejada.\n\n"
                f"Agar to'lovlar haqida ko'proq ma'lumot kerak bo'lsa:\n"
                f"💳 To'lovlar tarixi → Barcha to'lovlarni ko'rish\n"
                f"📄 Mening shartnomalarim → Shartnomalar va to'lov jadvali",
                reply_markup=main_menu_keyboard()
            )
            return

        # ✅ YANGI: Har bir shartnoma uchun mahsulot ma'lumotlarini olish
        # Barcha shartnomalarni olish
        from app.services.erpnext_api import erp_get_my_contracts_by_telegram_id
        contracts_data = await erp_get_my_contracts_by_telegram_id(telegram_id)

        # Contract ID bo'yicha mahsulotlarni dict'ga saqlash
        contracts_products = {}
        if contracts_data and contracts_data.get("success"):
            for contract in contracts_data.get("contracts", []):
                cid = contract.get("contract_id")
                products = contract.get("products", [])
                if cid:
                    contracts_products[cid] = products

        # Eslatmalar bor - formatlash
        message = f"🔔 <b>ESLATMALAR</b>\n\n"
        message += f"👤 <b>{customer_name}</b>\n\n"
        message += f"Sizda <b>{len(reminders)}</b> ta yaqin to'lov:\n\n"

        # Har bir eslatma uchun
        for i, reminder in enumerate(reminders, 1):
            contract_id = reminder.get("contract_id", "—")
            due_date = reminder.get("due_date", "—")
            amount = reminder.get("amount", 0)
            outstanding = reminder.get("outstanding", 0)
            days_left = reminder.get("days_left", 0)
            status = reminder.get("status", "upcoming")
            status_uz = reminder.get("status_uz", "")
            payment_number = reminder.get("payment_number", "")

            # Status emoji
            if status in ("critically_overdue", "overdue"):
                emoji = "⚠️"
            elif status == "today":
                emoji = "🔴"
            elif status == "tomorrow":
                emoji = "🟡"
            elif status == "soon":
                emoji = "🟢"
            else:
                emoji = "⚪"

            # Eslatma qatori
            message += f"{emoji} <b>{i}. Shartnoma {contract_id}</b>\n"

            # ✅ MAHSULOTLAR (agar mavjud bo'lsa)
            products = contracts_products.get(contract_id, [])
            if products:
                message += f"   🛍 Mahsulotlar:\n"
                for p in products[:10]:  # Faqat birinchi 2 ta
                    p_name = p.get("name", "—")
                    p_qty = p.get("qty", 0)
                    message += f"      • {p_name} ({p_qty} dona)\n"
                if len(products) > 2:
                    message += f"      • ... va yana {len(products) - 2} ta\n"

            message += f"   📅 To'lov sanasi: <b>{due_date}</b>\n"
            message += f"   💰 To'lov summasi: <b>${format_money(amount)}</b>\n"

            # Agar qoldiq bor bo'lsa
            if outstanding > 0:
                message += f"   📊 Qoldiq: <b>${format_money(outstanding)}</b>\n"

            # Status
            message += f"   ⏰ {status_uz}\n"

            # Separator
            if i < len(reminders):
                message += "\n"

        # Footer
        message += "\n━━━━━━━━━━━━━━━━━━━━\n"
        message += "ℹ️ To'lovni vaqtida amalga oshirishni unutmang.\n"
        message += "💳 Batafsil: <b>To'lovlar tarixi</b> tugmasini bosing"

        await msg.answer(
            message,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )

        logger.success(
            f"Reminders shown to {telegram_id}: {len(reminders)} reminders"
        )

    except Exception as e:
        logger.error(f"Reminders handler error for {telegram_id}: {e}")
        logger.exception("Full traceback:")

        await msg.answer(
            "❌ <b>Xatolik yuz berdi</b>\n\n"
            "Eslatmalarni yuklashda muammo bo'ldi. Iltimos, biroz kutib qaytadan urinib ko'ring.\n\n"
            "Agar muammo davom etsa, administratorga murojaat qiling.",
            reply_markup=main_menu_keyboard()
        )


def register_reminders_handlers(dp):
    """
    Reminders handler'ni dispatcher'ga ulash.

    Args:
        dp: Dispatcher instance
    """
    dp.include_router(router)
    router.message.register(show_reminders, F.text == "📅 Eslatmalar")
