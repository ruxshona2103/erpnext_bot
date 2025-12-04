from aiogram import Dispatcher
from .start import register_start_handlers
from .passport import register_passport_handlers
from .menu import register_menu_handlers
from .contract import register_contract_handlers
from .payments import register_payment_handlers
from .reminders_handler import register_reminders_handlers
from .unknown import register_unknown_handlers


def register_all_handlers(dp: Dispatcher):
    """
    Barcha handler'larni to'g'ri tartibda register qilish.

    Handler Priority (Yuqoridan pastga):
    ------------------------------------
    1. Commands (/start, /help) - Eng yuqori prioritet
    2. Menu tugmalari (Aniq text match)
    3. Specific handlers (Contracts, Payments, Reminders)
    4. Passport input handler (State-based)
    5. Unknown message handler - ENG PAST PRIORITET ⚠️

    ⚠️ DIQQAT: Tartibni o'zgartirish handler'lar ishlashini buzishi mumkin!
    """
    # 1. Commands - Eng birinchi (yuqori prioritet)
    register_start_handlers(dp)

    # 2. Menu tugmalari va specific handler'lar
    register_menu_handlers(dp)
    register_contract_handlers(dp)
    register_payment_handlers(dp)
    register_reminders_handlers(dp)

    # 3. Passport handler (State-based, lekin ancha keng filter)
    register_passport_handlers(dp)

    # 4. Unknown message handler - ENG OXIRIDA! (eng past prioritet)
    # Bu handler barcha qolgan xabarlarni ushlaydi
    register_unknown_handlers(dp)