from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from app.services.erpnext_api import (
    erp_get_contracts_by_telegram_id,
    erp_get_payment_history_with_products,
    erp_get_payment_schedule,
    erp_get_contract_details,
)
from app.utils.keyboard import main_menu_keyboard, contract_list_keyboard
from app.utils.formatters import (
    format_payment_history_with_products,
    format_detailed_payment_history,
)
from app.services.support import get_support_contact

router = Router()


async def payment_menu(msg: Message, state: FSMContext):
    """
    ✅ YANGI: Telegram ID orqali shartnomalar ro'yxatini ko'rsatish.

    Passport KERAK EMAS - user allaqachon /start da bog'langan!
    """
    telegram_id = msg.from_user.id

    logger.info(f"[Payment Menu] User {telegram_id} requested payment history")

    await msg.answer("🔎 Shartnomalar yuklanmoqda...")

    # Telegram ID orqali shartnomalarni olamiz
    data = await erp_get_contracts_by_telegram_id(telegram_id)

    logger.info(f"[Payment Menu] API response: success={data.get('success') if data else None}")

    if not data or not data.get("success"):
        # Xato xabarini log qilish
        error_msg = data.get("message", "Unknown error") if data else "No response"
        logger.warning(f"[Payment Menu] Failed for user {telegram_id}: {error_msg}")

        await msg.answer(
            "❌ <b>Sizning Telegram hisobingiz ERPNext mijoziga bog'lanmagan.</b>\n\n"
            "Avval /start bosib, passport raqamingizni kiriting.\n\n"
            f"<i>Debug: telegram_id={telegram_id}</i>",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        return

    contracts = data.get("contracts", [])
    logger.info(f"[Payment Menu] Found {len(contracts)} contracts for user {telegram_id}")

    if not contracts:
        await msg.answer(
            "📄 Sizda shartnomalar mavjud emas.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    # Shartnomalar ro'yxatini ko'rsatish
    await msg.answer(
        f"📄 Sizda <b>{len(contracts)}</b> ta shartnoma mavjud.\n"
        "To'lovlar tarixini ko'rish uchun shartnomani tanlang:",
        reply_markup=contract_list_keyboard(contracts, callback_prefix="payment"),
        parse_mode="HTML"
    )

    await state.clear()


async def show_payment_history(callback: CallbackQuery, state: FSMContext):
    """
    ✅ YANGILANGAN: Batafsil to'lovlar tarixi

    Ko'rsatiladi:
    - Shartnoma ma'lumotlari
    - Mahsulotlar (nomi, miqdori, narxi, IMEI)
    - Necha oylik muddatga kelishilgan
    - Qaysi oylar to'langan / to'lanmagan
    - Oxirgi to'lov sanasi va summasi
    - Umumiy statistika (jami, to'langan, qoldiq)
    """
    contract_id = callback.data.split(":")[1]

    try:
        await callback.message.edit_text(
            f"⏳ {contract_id} bo'yicha batafsil ma'lumotlar yuklanmoqda..."
        )
    except Exception:
        pass  # Message might already be deleted

    try:
        import asyncio

        # Parallel API calls
        logger.info(f"Fetching payment history for contract: {contract_id}")

        results = await asyncio.gather(
            erp_get_payment_history_with_products(contract_id),
            erp_get_payment_schedule(contract_id),
            return_exceptions=True
        )

        contract_data = results[0]
        schedule_data = results[1]

        # Contract data tekshirish
        if isinstance(contract_data, Exception):
            logger.error(f"Contract data exception: {contract_data}")
            contract_data = None

        if isinstance(schedule_data, Exception):
            logger.error(f"Schedule data exception: {schedule_data}")
            schedule_data = None

        # Debug log
        logger.debug(f"Contract data: {contract_data}")
        logger.debug(f"Schedule data: {schedule_data}")

        # Agar asosiy data topilmasa
        if not contract_data or not isinstance(contract_data, dict) or not contract_data.get("success"):
            error_msg = "Shartnoma ma'lumotlari topilmadi"
            if contract_data and isinstance(contract_data, dict):
                error_msg = contract_data.get("message", error_msg)

            await callback.message.answer(
                f"❌ {error_msg}",
                reply_markup=main_menu_keyboard()
            )
            return

        # Schedule data xavfsiz olish
        safe_schedule_data = {"schedule": [], "success": False}
        if schedule_data and isinstance(schedule_data, dict):
            if schedule_data.get("success"):
                safe_schedule_data = schedule_data
            elif schedule_data.get("schedule"):
                safe_schedule_data = {"schedule": schedule_data.get("schedule", []), "success": True}

        # Payment history data tayyorlash
        payment_history_data = {
            "payments": contract_data.get("payments", []),
            "total_payments": contract_data.get("total_payments", 0)
        }

        logger.info(f"Formatting detailed payment history for {contract_id}")
        logger.info(f"Products count: {len(contract_data.get('products', []))}")
        logger.info(f"Payments count: {len(payment_history_data.get('payments', []))}")
        logger.info(f"Schedule count: {len(safe_schedule_data.get('schedule', []))}")

        # ✅ Batafsil formatter ishlatish
        formatted = format_detailed_payment_history(
            contract_data=contract_data,
            schedule_data=safe_schedule_data,
            payment_history_data=payment_history_data
        )

        # Xabar uzunligini tekshirish (Telegram 4096 limit)
        if len(formatted) > 4000:
            # Xabarni bo'laklarga ajratamiz
            parts = split_long_message(formatted)
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    # Oxirgi qism - keyboard bilan
                    await callback.message.answer(
                        part,
                        reply_markup=main_menu_keyboard(),
                        parse_mode="HTML"
                    )
                else:
                    await callback.message.answer(part, parse_mode="HTML")
        else:
            await callback.message.answer(
                formatted,
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )

        logger.success(f"Detailed payment history shown for {contract_id}")

    except Exception as e:
        logger.error(f"show_payment_history error for {contract_id}: {e}")
        logger.exception("Full traceback:")

        # Operator telefon raqamini olish
        support = await get_support_contact()

        await callback.message.answer(
            "❌ <b>Xatolik yuz berdi</b>\n\n"
            "Ma'lumotlarni yuklashda muammo bo'ldi. "
            "Iltimos, qaytadan urinib ko'ring.\n\n"
            f"Agar muammo davom etsa, {support['name']}'ga murojaat qiling:\n"
            f"📞 {support['phone']}",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )


def split_long_message(text: str, max_length: int = 4000) -> list:
    """
    Uzun xabarni bo'laklarga ajratish.

    Args:
        text: Uzun xabar matni
        max_length: Maksimal uzunlik (default 4000)

    Returns:
        List of message parts
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = ""

    # Bo'laklarga ajratish (satrlar bo'yicha)
    lines = text.split("\n")

    for line in lines:
        if len(current_part) + len(line) + 1 <= max_length:
            current_part += line + "\n"
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = line + "\n"

    if current_part:
        parts.append(current_part.strip())

    return parts


def register_payment_handlers(dp):
    """
    Payment handler'larni register qilish.

    DIQQAT: Tugma nomi keyboard'da "💳 To'lovlar tarixi" (ko'plik shakli)!
    """
    dp.include_router(router)

    # ✅ TUZATILDI: "To'lovlar tarixi" (ko'plik) - keyboard'ga mos keladi
    router.message.register(payment_menu, F.text == "💳 To'lovlar tarixi")
    router.callback_query.register(show_payment_history, F.data.startswith("payment:"))
