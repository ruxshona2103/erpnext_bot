from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.erpnext_api import (
    erp_get_customer_by_passport,
    erp_get_contract_details,
    erp_get_payment_schedule,  # ✅ YANGI: To'lov jadvali uchun
)
from app.utils.keyboard import main_menu_keyboard, contract_list_keyboard
from app.utils.formatters import format_contract_details, format_money
from app.states.user_states import ContractState, PassportState

router = Router()


# ❌ ESKI - PASSPORT SO'RASH (kerak emas!)
# Bu function endi ishlatilmaydi - faqat telegram ID ishlatamiz
# async def contract_menu(msg: Message, state: FSMContext):
#     await msg.answer("🔍 Iltimos passport raqamingizni kiriting:")
#     await state.set_state(PassportState.waiting_for_passport)


# ✅ YANGI - TELEGRAM ID ISHLATISH
async def contract_menu(msg: Message, state: FSMContext):
    """
    Shartnomalar menyusi - PASSPORT KERAK EMAS!

    Telegram ID orqali to'g'ridan-to'g'ri shartnomalarni olamiz.
    User allaqachon /start da passport kiritgan, shuning uchun
    qaytadan so'rash kerak emas.
    """
    telegram_id = msg.from_user.id

    # ✅ DEBUG: Log telegram_id
    from loguru import logger
    logger.info(f"Contract menu requested by telegram_id: {telegram_id}")

    await msg.answer("🔎 Shartnomalar yuklanmoqda...")

    # ✅ YANGI: To'g'ridan-to'g'ri get_my_contracts_by_telegram_id ni chaqiramiz
    from app.services.erpnext_api import erp_get_my_contracts_by_telegram_id

    response = await erp_get_my_contracts_by_telegram_id(telegram_id)

    # ✅ DEBUG: Response'ni log qilish
    logger.debug(f"API Response: success={response.get('success')}, customer={response.get('customer_id')}")

    if not response or not response.get("success"):
        # ✅ DEBUG: Xato sababini ko'rsatish
        error_msg = response.get("message", "Noma'lum xato") if response else "API javob bermadi"
        logger.error(f"Failed to get contracts: {error_msg}")

        await msg.answer(
            f"❌ <b>Sizning Telegram hisobingiz ERPNext mijoziga bog'lanmagan</b>\n\n"
            f"<b>Sabab:</b> {error_msg}\n\n"
            f"<b>Yechim:</b>\n"
            f"1. /start bosing\n"
            f"2. Passport raqamingizni kiriting\n"
            f"3. Qaytadan urinib ko'ring\n\n"
            f"<i>Agar muammo davom etsa, admin bilan bog'laning.</i>\n"
            f"<i>Telegram ID: <code>{telegram_id}</code></i>",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        return

    contracts = response.get("contracts", [])
    customer_name = response.get("customer_name", "Mijoz")

    if not contracts:
        await msg.answer(
            f"📄 <b>{customer_name}</b>, sizda shartnomalar mavjud emas.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    # ✅ YANGI: Batafsil shartnomalarni formatlab ko'rsatish (mahsulotlar + TO'LOV JADVALI bilan)
    import asyncio

    for contract in contracts:
        contract_id = contract.get("contract_id", "—")
        contract_date = contract.get("contract_date", "—")
        total_amount = contract.get("total_amount", 0)
        paid = contract.get("paid", 0)
        remaining = contract.get("remaining", 0)
        products = contract.get("products", [])
        next_payment = contract.get("next_payment")

        # ✅ YANGI: To'lov jadvalini olish
        schedule_data = await erp_get_payment_schedule(contract_id)
        schedule = schedule_data.get("schedule", []) if schedule_data.get("success") else []

        # Shartnoma ma'lumotlari
        message = f"━━━━━━━━━━━━━━━━━━━━\n"
        message += f"📄 <b>SHARTNOMA: {contract_id}</b>\n"
        message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"📅 Tuzilgan sana: <b>{contract_date}</b>\n\n"
        message += f"💰 Umumiy summa: <b>{format_money(total_amount)}</b> so'm\n"
        message += f"✅ To'langan: <b>{format_money(paid)}</b> so'm\n"
        message += f"📉 Qoldiq: <b>{format_money(remaining)}</b> so'm\n"

        # To'lov foizi
        if total_amount > 0:
            percentage = (paid / total_amount) * 100
            message += f"📊 To'lov foizi: <b>{percentage:.1f}%</b>\n"

        # ✅ MAHSULOTLAR
        if products:
            message += f"\n━━━━━━━━━━━━━━━━━━━━\n"
            message += f"🛍 <b>MAHSULOTLAR ({len(products)} ta)</b>\n"
            message += f"━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, p in enumerate(products, 1):
                p_name = p.get("name", "—")
                p_qty = p.get("qty", 0)
                p_imei = p.get("imei", "")

                message += f"<b>{i}. {p_name}</b> — {p_qty} dona\n"
                if p_imei:
                    message += f"   🔢 IMEI: <code>{p_imei}</code>\n"

        # ✅ YANGI: TO'LOV JADVALI (qaysi kunlari to'lov qilish kerak)
        if schedule:
            total_months = len(schedule)
            paid_months = len([s for s in schedule if s.get("status") == "paid"])
            overdue_months = len([s for s in schedule if s.get("is_overdue")])

            message += f"\n━━━━━━━━━━━━━━━━━━━━\n"
            message += f"📅 <b>TO'LOV JADVALI ({total_months} oylik)</b>\n"
            message += f"━━━━━━━━━━━━━━━━━━━━\n\n"

            message += f"✅ To'langan oylar: <b>{paid_months}</b> ta\n"
            message += f"⏳ Qolgan oylar: <b>{total_months - paid_months}</b> ta\n"
            if overdue_months > 0:
                message += f"❌ Kechikkan: <b>{overdue_months}</b> ta\n"

            message += f"\n<b>Oylar tafsiloti:</b>\n\n"

            for month in schedule:
                month_num = month.get("month", 0)
                due_date = month.get("due_date", "—")
                amount = month.get("amount", 0)
                month_paid = month.get("paid", 0)
                outstanding = month.get("outstanding", 0)
                status = month.get("status", "pending")
                is_overdue = month.get("is_overdue", False)

                # Status emoji va text
                if status == "paid":
                    emoji = "✅"
                    status_text = "To'langan"
                elif status == "partial":
                    emoji = "⚠️"
                    status_text = f"Qisman ({format_money(month_paid)} so'm)"
                elif is_overdue:
                    emoji = "❌"
                    status_text = "Kechikkan!"
                else:
                    emoji = "⏳"
                    status_text = "Kutilmoqda"

                message += f"{emoji} <b>{month_num}-oy</b> | {due_date}\n"
                message += f"   💵 {format_money(amount)} so'm — {status_text}\n"

                if outstanding > 0 and status != "paid":
                    message += f"   📉 Qoldiq: {format_money(outstanding)} so'm\n"

        # ✅ KEYINGI TO'LOV (qisqa xulosa)
        elif next_payment:
            message += f"\n━━━━━━━━━━━━━━━━━━━━\n"
            message += f"📅 <b>KEYINGI TO'LOV:</b>\n"
            message += f"   📆 Muddat: <b>{next_payment.get('due_date', '—')}</b>\n"
            message += f"   💰 Summa: <b>{format_money(next_payment.get('amount', 0))}</b> so'm\n"
            message += f"   ⏰ {next_payment.get('status_uz', 'Kutilmoqda')}\n"

        message += f"\n━━━━━━━━━━━━━━━━━━━━"

        await msg.answer(
            message,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )

    await state.clear()


# 3️⃣ CALLBACK → bitta kontrakt detali
async def kontrakt_details(call: CallbackQuery, state: FSMContext):
    data = call.data.split(":")
    contract_id = data[1]

    await call.message.edit_text(
        "⏳ Shartnoma ma'lumotlari yuklanmoqda..."
    )

    # API chaqiramiz
    response = await erp_get_contract_details(contract_id)

    if not response or not response.get("success"):
        await call.message.answer(
            "❌ Shartnoma topilmadi.",
            reply_markup=main_menu_keyboard()
        )
        return

    # Formatlangan shartnoma
    formatted = format_contract_details(response)

    await call.message.answer(
        formatted,
        reply_markup=main_menu_keyboard()
    )

    await state.clear()


# REGISTER
def register_contract_handlers(dp):
    dp.include_router(router)

    # ✅ Faqat telegram ID ishlatamiz - passport kerak emas
    router.message.register(contract_menu, F.text == "📄 Mening shartnomalarim")
    # ❌ ESKI: contract_passport_received o'chirildi - kerak emas
    router.callback_query.register(kontrakt_details, F.data.startswith("contract:"))
