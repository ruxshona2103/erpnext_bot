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


#USER “Mening shartnomalarim” ni bosadi
async def contract_menu(msg: Message, state: FSMContext):
    await msg.answer("🔍 Iltimos passport raqamingizni kiriting:")
    await state.set_state(PassportState.waiting_for_passport)


#USER PASSPORTNI KIRITADI → kontrakt ro‘yxati
async def contract_passport_received(msg: Message, state: FSMContext):
    passport = msg.text.strip().upper()
    await msg.answer("⏳ Ma'lumotlar yuklanmoqda...")

    # API chaqiramiz
    response = await erp_get_customer_by_passport(passport)

    if not response or not response.get("success"):
        await msg.answer(
            "❌ Mijoz topilmadi. Iltimos passport raqamini qayta kiriting.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        return

    contracts = response.get("contracts", [])

    if not contracts:
        await msg.answer(
            "📄 Sizda shartnomalar mavjud emas.",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    # INLINE RO‘YXAT YUBORISH
    await msg.answer(
        "📄 Sizning shartnomalaringiz ro‘yxati:",
        reply_markup=contract_list_keyboard(contracts)
    )

    await state.set_state(ContractState.selecting_contract)


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

    router.message.register(contract_menu, F.text == "📄 Mening shartnomalarim")
    router.message.register(contract_passport_received, PassportState.waiting_for_passport)
    router.callback_query.register(kontrakt_details, F.data.startswith("contract:"))
