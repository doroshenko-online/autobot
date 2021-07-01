from aiogram.dispatcher.filters.state import State, StatesGroup


class StateNumber(StatesGroup):
    wait_for_state_number = State()