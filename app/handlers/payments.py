from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.states.user_states import PassportState
from app.services.erpnext_api import (
    erp_get_customer_by_passport,
    erp_get_payment_history,
)
from app.utils.keyboard import main_menu_keyboard, contract_list_keyboard
from app.utils.formatters import format_payment_history

router = Router()


async def payment_menu(msg: Message, state: FSMContext):
    await msg.answer(
        "💳 To'lovlar tarixini olish uchun passport raqamini yuboring.\n"
        "Masalan: <b>AA1234567</b>"
    )
    await state.set_state(PassportState.waiting_for_passport)


async def payments_passport_received(msg: Message, state: FSMContext):
    passport = msg.text.strip().upper()

    await msg.answer("🔎 Mijoz ma'lumotlari yuklanmoqda...")

    data = await erp_get_customer_by_passport(passport)

    if not data or not data.get("success"):
        await msg.answer("❌ Mijoz topilmadi.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    customer = data["customer"]
    customer_id = customer["name"]       # ← TO‘G‘RI joyi

    contracts = data["contracts"]["contracts"]

    if not contracts:
        await msg.answer("📄 Sizda shartnomalar yo‘q.", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    await msg.answer(
        "📄 Shartnomalardan birini tanlang:",
        reply_markup=contract_list_keyboard(contracts)
    )

    await state.update_data(customer=customer_id)
    await state.clear()


async def show_payment_history(callback: CallbackQuery, state: FSMContext):
    contract_id = callback.data.split(":")[1]

    await callback.message.answer(
        f"⏳ {contract_id} bo‘yicha to‘lovlar yuklanmoqda..."
    )

    data = await erp_get_payment_history(contract_id)

    if not data or not data.get("success"):
        await callback.message.answer(
            "❌ To‘lovlar topilmadi.",
            reply_markup=main_menu_keyboard()
        )
        return

    formatted = format_payment_history(data)

    await callback.message.answer(formatted, reply_markup=main_menu_keyboard())


def register_payment_handlers(dp):
    dp.include_router(router)

    router.message.register(payment_menu, F.text == "💳 To'lovlar tarixi")
    router.message.register(payments_passport_received, PassportState.waiting_for_passport)
    router.callback_query.register(show_payment_history, F.data.startswith("contract:"))
