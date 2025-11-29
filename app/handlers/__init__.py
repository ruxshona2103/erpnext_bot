from aiogram import Dispatcher
from .start import register_start_handlers
from .passport import register_passport_handlers
from .menu import register_menu_handlers
from .contract import register_contract_handlers
from .payments import register_payment_handlers
from .reminders_handler import register_reminders_handlers


def register_all_handlers(dp: Dispatcher):
    # 1. Tugmalar (Aniq buyruqlar) - BULAR BIRINCHI TURISHI SHART
    register_start_handlers(dp)
    register_menu_handlers(dp)      # <-- Menyular
    register_contract_handlers(dp)
    register_payment_handlers(dp)
    register_reminders_handlers(dp)

    # 2. Passport tekshiruvi (Umumiy buyruq) - BU ENG OXIRIDA TURISHI SHART
    register_passport_handlers(dp)