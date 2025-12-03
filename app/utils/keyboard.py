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
            [KeyboardButton(text="👤 Mening profilim")],
            [KeyboardButton(text="📄 Mening shartnomalarim")],
            [KeyboardButton(text="💳 To'lovlar tarixi")],
            [KeyboardButton(text="📅 Eslatmalar")],
            [KeyboardButton(text="❓ Yordam")],
        ]
    )


#CONTRACT LIST (Inline Keyboard)
def contract_list_keyboard(contracts: list, callback_prefix: str = "contract"):
    buttons = []

    # Har bir shartnoma uchun button
    for c in contracts:
        # ERPNext API dan contract_id keladi
        cid = c.get("contract_id") or c.get("id") or c.get("name")
        if cid:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📄 {cid}",
                    callback_data=f"{callback_prefix}:{cid}"  # ← YANGI: prefix parametri
                )
            ])

    # Orqaga tugma
    buttons.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back:menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


#CONTRACT DETAIL (Inline Keyboard)
def contract_detail_keyboard(contract_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📅 To'lov jadvalim",
                callback_data=f"schedule:{contract_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 To'lovlar tarixi",
                callback_data=f"payments:{contract_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Orqaga",
                callback_data="back:contracts"
            )
        ]
    ])



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
