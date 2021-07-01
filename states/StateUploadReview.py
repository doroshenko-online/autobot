from aiogram.dispatcher.filters.state import State, StatesGroup


class UploadReview(StatesGroup):
    wait_for_video_name = State()
    wait_for_video = State()
    wait_confirm = State()