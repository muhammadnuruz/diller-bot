from aiogram.fsm.state import State, StatesGroup

class StartState(StatesGroup):
    url = State()
    login = State()
    password = State()
    type_price = State()