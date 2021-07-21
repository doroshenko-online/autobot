from aiogram.dispatcher.filters.state import State, StatesGroup


class AddAdmin(StatesGroup):
    wait_for_chat_id = State()
