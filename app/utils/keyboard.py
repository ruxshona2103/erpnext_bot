from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


#MAIN MENU (Reply Keyboard)
def main_menu_keyboard():
    """
    Foydalanuvchi uchun asosiy menyu.
    ERPNext bot logikasi uchun moslangan yakuniy variant.
    """
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="🔍 Passport orqali qidirish")],
            [KeyboardButton(text="📄 Mening shartnomalarim")],
            [KeyboardButton(text="💳 To'lovlar tarixi")],
            [KeyboardButton(text="📅 Eslatmalar")],
        ]
    )


#CONTRACT LIST (Inline Keyboard)
def contract_list_keyboard(contracts: list):
    """
    Contract ro‘yxati — foydalanuvchi birini tanlaydi.
    contracts = [
        {"id": "SO-0001"},
        {"id": "SO-0002"},
        ...
    ]
    """
    kb = InlineKeyboardMarkup()

    for c in contracts:
        cid = c.get("id")
        kb.add(
            InlineKeyboardButton(
                text=f"📄 Shartnoma {cid}",
                callback_data=f"contract:{cid}"
            )
        )

    kb.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back:menu"))
    return kb


#CONTRACT DETAIL (Inline Keyboard)
def contract_detail_keyboard(contract_id: str):
    """
    Shartnoma ichki menyusi:
    - To‘lov jadvali
    - To‘lovlar tarixi
    - Orqaga
    """
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(
            text="📅 To‘lov jadvali",
            callback_data=f"schedule:{contract_id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="💳 To‘lovlar tarixi",
            callback_data=f"payments:{contract_id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="back:contracts"
        )
    )

    return kb



#PAYMENT HISTORY BACK BUTTON
def payment_history_keyboard(contract_id: str):
    """
    To'lovlar tarixidan orqaga qaytish.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data=f"contract:{contract_id}"
            )
        ]
    ])


#PAYMENT SCHEDULE BACK BUTTON
def schedule_keyboard(contract_id: str):
    """
    To‘lov jadvalidan orqaga qaytish.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data=f"contract:{contract_id}"
            )
        ]
    ])


# UNIVERSAL BACK BUTTON (optional)
def back_button(callback: str = "back:menu"):
    """
    Universa orqaga tugma.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=callback)]
    ])
