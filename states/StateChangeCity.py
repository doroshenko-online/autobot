from aiogram.dispatcher.filters.state import State, StatesGroup


class ChangeCity(StatesGroup):
    wait_for_city_name = State()
    wait_for_city_ukr_name = State()
    wait_for_city_dir_id = State()