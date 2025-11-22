from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.erpnext_api import (
    erp_get_customer_by_passport,
    erp_get_contract_details
)
from app.utils.keyboard import main_menu_keyboard, contract_list_keyboard
from app.utils.formatters import format_contract_details
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

    # ✅ YANGI: Batafsil shartnomalarni formatlab ko'rsatish (mahsulotlar bilan)
    for contract in contracts:
        contract_id = contract.get("contract_id", "—")
        contract_date = contract.get("contract_date", "—")
        total_amount = contract.get("total_amount", 0)
        paid = contract.get("paid", 0)
        remaining = contract.get("remaining", 0)
        products = contract.get("products", [])
        next_payment = contract.get("next_payment")

        # Format money
        from app.utils.formatters import format_money

        # Shartnoma ma'lumotlari
        message = f"📄 <b>SHARTNOMA: {contract_id}</b>\n\n"
        message += f"📅 Sana: <b>{contract_date}</b>\n"
        message += f"💰 Jami summa: <b>{format_money(total_amount)}</b> so'm\n"
        message += f"✅ To'langan: <b>{format_money(paid)}</b> so'm\n"
        message += f"📉 Qoldiq: <b>{format_money(remaining)}</b> so'm\n\n"

        # ✅ MAHSULOTLAR
        if products:
            message += f"🛍 <b>MAHSULOTLAR ({len(products)} ta):</b>\n"
            for i, p in enumerate(products, 1):
                p_name = p.get("name", "—")
                p_qty = p.get("qty", 0)
                p_price = p.get("price", 0)
                p_imei = p.get("imei", "")

                message += f"\n<b>{i}. {p_name}</b>\n"
                message += f"   📦 Miqdor: {p_qty} dona\n"
                message += f"   💵 Narx: {format_money(p_price)} so'm\n"
                if p_imei:
                    message += f"   🔢 IMEI: <code>{p_imei}</code>\n"

        # ✅ KEYINGI TO'LOV
        if next_payment:
            message += f"\n━━━━━━━━━━━━━━━━━━━━\n"
            message += f"📅 <b>KEYINGI TO'LOV:</b>\n"
            message += f"   📆 Muddat: <b>{next_payment.get('due_date', '—')}</b>\n"
            message += f"   💰 Summa: <b>{format_money(next_payment.get('amount', 0))}</b> so'm\n"
            message += f"   ⏰ {next_payment.get('status_uz', 'Kutilmoqda')}\n"

        await msg.answer(
            message,
            reply_markup=main_menu_keyboard()
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
