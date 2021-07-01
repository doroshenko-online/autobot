from aiogram.dispatcher.filters.state import State, StatesGroup


class StateCity(StatesGroup):
    wait_for_city = State()
    wait_for_change_city = State()