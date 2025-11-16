from aiogram.fsm.state import StatesGroup ,State

class PassportState(StatesGroup):
    """ FSM State passport raqami uchun"""
    waiting_for_passport = State()

class ContractState(StatesGroup):
    """FSM State shartnoma malumotlari uchun"""
    selecting_contract = State()
    viewing_contract = State()

class PaymentState(StatesGroup):
    """ FSM State tolov tarixi va filterlash uchun"""
    selecting_period = State()

class ReminderState(StatesGroup):
    """FSM State notification yuborib turish uchun"""
    setting_reminder = State()
