from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from app.utils.keyboard import main_menu_keyboard

router = Router()


async def start_message(msg: Message):
    user = msg.from_user

    text = (
        f"Assalomu alaykum, <b>{user.full_name}</b> 👋\n\n"
        "📌 Bu bot orqali siz quyidagi ma'lumotlarni olishingiz mumkin:\n"
        "• Shaxsiy ma'lumotlar\n"
        "• Shartnomalar\n"
        "• To'lov tarixi\n"
        "• To'lov kuniga eslatma\n\n"
        "🔐 Davom etish uchun pastdagi tugmalardan foydalaning.\n"
    )

    await msg.answer(text, reply_markup=main_menu_keyboard())


def register_start_handlers(dp):
    dp.include_router(router)

    router.message.register(start_message, CommandStart())

