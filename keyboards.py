from aiogram import types
from misc import *
from core.Register import Registry


def start_text(chat_id):
    chat_id = str(chat_id)
    text = ''
    user = Registry.get_user(chat_id)
    if user is None:
        text += 'Оберіть місто'

    elif user.isdriver():
        text += '⬇ Оберіть дію'

    else:
        text += '⬇ выберите действие'

    return text


def start_keyboard(chat_id):
    chat_id = str(chat_id)
    kb = types.ReplyKeyboardMarkup(row_width=1)
    user = Registry.get_user(chat_id)

    if user is None:
        kb.add('👉 Оберіть місто')

    elif user.isdriver():
        state_number = user.getstatenumber()
        kb.add('↪ Вказати інше місто')
        if state_number == '' or state_number is None:
            kb.add('🛠 Вказати реєстраційний номер авто')
        else:
            kb.add('🔂 Вказати інший номер реєстрації')
            kb.add('🆕 Завантажити огляд')

    elif user.isregionuser():
        kb.add('👿 Показать заблокированных водителей по городу ' + user.city.name)
        kb.add('🆕 Загрузить осмотр')

    elif user.isadmin():
        kb.add('🌆 Добавить город')
        kb.add('👁 Показать все города')
        kb.add('🧔 Добавить администратора')
        kb.add('🐕 Добавить региональный аккаунт')

    return kb


def cancel_text_func():
    return "Чтобы отменить действие введите команду /cancel или нажмите на кнопку 'Отмена'"


def cancel_text_func_ukr():
    return "Для скасування - натисніть кнопку «Скасувати» або введіть /cancel"


def cancel_keyboard():
    kb = types.ReplyKeyboardMarkup(row_width=1)
    kb.add('Отмена')
    return kb


def cancel_keyboard_ukr():
    kb = types.ReplyKeyboardMarkup(row_width=1)
    kb.add('Скасувати')
    return kb


def confirm_keyboard():
    kb = types.ReplyKeyboardMarkup(row_width=2)
    kb.row('✅ Да', '🛑 Нет')
    kb.add('Отмена')
    return kb


def confirm_keyboard_ukr():
    kb = types.ReplyKeyboardMarkup(row_width=2)
    kb.row('✅ Так', '🛑 Ні')
    kb.add('Скасувати')
    return kb


def city_inline_keyboard(admin=False):
    kb = types.InlineKeyboardMarkup(row_width=1)
    if admin:
        for city_id, city in Registry.cities.items():
            kb.add(types.InlineKeyboardButton(city.name, callback_data=f'show_city_id:{city_id}'))
    else:
        for city_id, city in Registry.cities.items():
            kb.add(types.InlineKeyboardButton(city.name, callback_data=f'city_id:{city_id}'))

    return kb


def change_city_inline_keyboard(city_id):
    kb = types.InlineKeyboardMarkup()
    for cid, city in Registry.cities.items():
        if cid == city_id:
            kb.add(types.InlineKeyboardButton(city.name, callback_data=f'selected_show_city_id:{city_id}'))
            inline_btn1 = types.InlineKeyboardButton('Изменить название', callback_data=f'change_city_name:{cid}')
            inline_btn2 = types.InlineKeyboardButton('Изменить украинское название', callback_data=f'change_city_ukr_name:{cid}')
            inline_btn3 = types.InlineKeyboardButton('Изменить id папки', callback_data=f'change_city_dir_id:{cid}')
            kb.add(inline_btn1, inline_btn2, inline_btn3)
        else:
            kb.add(types.InlineKeyboardButton(city.name, callback_data=f'show_city_id:{city_id}'))

    return kb


def get_blocked_drivers_kb_and_text(user):
    result = user.get_blocked_users()
    text = ''
    if not result:
        text += "Список пуст"
        kb = start_keyboard(user.chat_id)
        yield text, kb,
    else:
        for driver in result:
            yield "Username: @{0} | Гос. номер: {1}".format(driver[1], driver[2]), types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Разблокировать', callback_data=f'unblock_driver:{driver[0]}'))
