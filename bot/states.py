from aiogram.fsm.state import State, StatesGroup


class StartState(StatesGroup):
    url = State()
    login = State()
    password = State()
    type_price = State()


class PermissionState(StatesGroup):
    waiting_for_days = State()

class AdverbState(StatesGroup):
    none_adverb = State()
    forward_adverb = State()