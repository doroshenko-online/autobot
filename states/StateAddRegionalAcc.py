from aiogram.dispatcher.filters.state import State, StatesGroup


class AddRegionalAcc(StatesGroup):
    wait_for_chat_id = State()