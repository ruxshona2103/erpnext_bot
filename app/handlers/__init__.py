from aiogram import Dispatcher
from .start import register_start_handlers
from .passport import register_passport_handlers
from .menu import register_menu_handlers
from .contract import register_contract_handlers
from .payments import register_payment_handlers


def register_all_handlers(dp: Dispatcher):
    """
    Register all bot handlers here.
    Keeps the loader clean and modular.
    """

    register_start_handlers(dp)
    register_passport_handlers(dp)
    register_menu_handlers(dp)
    register_contract_handlers(dp)
    register_payment_handlers(dp)
