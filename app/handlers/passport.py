from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.utils.keyboard import main_menu_keyboard, contract_list_keyboard
from app.states.user_states import PassportState
from app.services.erpnext_api import erp_get_customer_by_passport

router = Router()


async def ask_passport(msg: Message, state: FSMContext):
    await state.set_state(PassportState.waiting_for_passport)
    await msg.answer(
        "✍️ Passport seriya + raqamini kiriting.\n"
        "Masalan: <b>AA1234567</b>"
    )


async def process_passport(msg: Message, state: FSMContext):
    passport = msg.text.strip().replace(" ", "").upper()

    await msg.answer("🔎 Ma'lumotlar tekshirilmoqda...")

    # API dan kelgan javobni json sifatida olish
    data = await erp_get_customer_by_passport(passport)

    # --- Agar API xato qaytargan bo‘lsa ---
    if not isinstance(data, dict):
        await msg.answer("❌ Serverdan noto‘g‘ri formatda javob qaytdi.")
        await state.clear()
        return

    # --- success False bo‘lsa ---
    if data.get("success") is not True:
        await msg.answer(
            f"❌ {data.get('message', 'Mijoz topilmadi')}\n"
            "♻️ Qayta urinib ko‘ring."
        )
        await state.clear()
        return

    # ---- CUSTOMER ----
    customer = data.get("customer", {})
    full_name = customer.get("customer_name", "Noma'lum")
    phone = customer.get("custom_phone_1", "—")
    customer_id = customer.get("name", "—")

    text = (
        f"👤 <b>{full_name}</b>\n"
        f"📞 Telefon: <code>{phone}</code>\n"
        f"🆔 ID: <code>{customer_id}</code>\n\n"
    )

    # ---- CONTRACTS ----
    contract_block = data.get("contracts", {})
    contract_list = contract_block.get("contracts", [])

    if contract_list:
        cleaned_contracts = []

        for c in contract_list:
            cleaned_contracts.append({
                "id": c.get("id") or c.get("name"),
                "date": c.get("date"),
                "total": c.get("total"),
                "remaining": c.get("remaining"),
            })

        text += (
            f"📄 Sizda <b>{len(cleaned_contracts)}</b> ta shartnoma mavjud.\n"
            "Quyidan birini tanlang:"
        )

        kb = contract_list_keyboard(cleaned_contracts)

    else:
        text += "📄 Sizga biriktirilgan shartnomalar mavjud emas."
        kb = main_menu_keyboard()

    # ===== SEND MESSAGE =====
    await msg.answer(text, reply_markup=kb)
    await state.clear()


def register_passport_handlers(dp):
    dp.include_router(router)

    router.message.register(ask_passport, F.text == "🔍 Passport orqali qidirish")
    router.message.register(process_passport, PassportState.waiting_for_passport)
