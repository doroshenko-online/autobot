from aiogram.types.message import Message
from init import *
from misc import *
import os
from keyboards import *
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from core.Loader import Loader
from core.City import City
from core.Register import Registry
from core.User import User
from states.StateCity import StateCity
from states.StateNumber import StateNumber
from states.StateAddCity import AddCity
from states.StateAddRegionalAcc import AddRegionalAcc
from states.StateUploadReview import UploadReview
from states.StateChangeCity import ChangeCity
from states.StateAddAdmin import AddAdmin

"""
Actions:

    Новые пользователи:
        👉 Выбрать город
        
    Водители:
        🛠 Указать гос. номер
        🔂 Сменить гос. номер
        ↪ Сменить город
        🆕 Загрузить осмотр
        
    Региональные аккаунты:
        👿 Показать заблокированных водителей по городу
        (inline) Заблокировать
        (inline) Разблокирвать
        🆕 Загрузить осмотр
        
    Администраторы:
        🌆 Добавить город
        (inline) Изменить город
        👁 Показать все города
        🧔 Добавить администратора
        🐕 Добавить региональный аккаунт    

"""

TOKEN = ''
memory_storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=memory_storage)
loader = Loader()


# ---------------- Общие обработчики
@dp.message_handler(commands=['start', 'help'])
async def start(msg: types.Message):
    text = start_text(msg.chat.id)
    keyboard = start_keyboard(msg.chat.id)
    await msg.answer(text, reply_markup=keyboard)


@dp.message_handler(commands=['id'])
async def get_id(msg: types.Message):
    await msg.answer(msg.chat.id)


@dp.message_handler(commands="cancel", state="*")
@dp.message_handler(Text(equals="Отмена", ignore_case=True), state="*")
async def cancel(msg: types.Message, state: FSMContext):
    message = start_text(msg.chat.id)
    keyboard = start_keyboard(msg.chat.id)
    await msg.answer("Действие отменено", reply_markup=None)
    await msg.answer(message, reply_markup=keyboard)
    await state.finish()


@dp.message_handler(Text(startswith="🆕", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def upload_review_start(msg: types.Message):
    user = Registry.get_user(msg.chat.id)
    cancel_kb = cancel_keyboard()
    cancel_text = cancel_text_func()
    if user:
        if user.isdriver():
            if user.isblocked():
                text = 'Вам временно не разрешено загружать осмотры. Обратитесь к своему менеджеру'
                await msg.answer(text)
                return
            else:
                text = 'Загрузите видео или снимите новое'
                await UploadReview.wait_for_video.set()

        if user.isregionuser():
            await UploadReview.wait_for_video_name.set()
            text = 'Введите название для видео, которое будет на гугл диске'

        if user.isadmin():
            return

        await msg.answer(text)
        await msg.answer(cancel_text, reply_markup=cancel_kb)
        

# Загрузка осмотра
@dp.message_handler(state=UploadReview.wait_for_video_name, content_types=types.ContentTypes.TEXT)
async def upload_video_processing_name(msg: types.Message, state: FSMContext):
    await state.update_data(video_name=str(msg.text).strip())
    text = 'Загрузите видео или снимите новое'
    await UploadReview.next()
    await msg.answer(text)


@dp.message_handler(state=UploadReview.wait_for_video, content_types=types.ContentTypes.VIDEO)
async def upload_video_processing(msg: Message, state: FSMContext):
    print(f'downloading video from {str(msg.chat.id)}')
    video = await msg.video.download(files_dir)
    mime_type = str(msg.video.mime_type)
    await state.update_data(mime_type=mime_type)
    video_path = video.name
    await state.update_data(video_path=video_path)
    await UploadReview.next()
    text = 'Отправить осмотр?'
    confirm_kb = confirm_keyboard()
    await msg.answer(text, reply_markup=confirm_kb)


@dp.message_handler(state=UploadReview.wait_for_video, content_types=types.ContentTypes.VIDEO_NOTE)
async def upload_video_note_processing(msg: Message, state: FSMContext):
    print(f'downloading video_note from {str(msg.chat.id)}')
    video = await msg.video_note.download(files_dir)
    video_path = video.name
    await state.update_data(video_path=video_path)
    await UploadReview.next()
    text = 'Отправить видео?'
    confirm_kb = confirm_keyboard()
    await msg.answer(text, reply_markup=confirm_kb)


@dp.message_handler(state=UploadReview.wait_confirm, content_types=types.ContentTypes.TEXT)
async def upload_video_confirm(msg: Message, state: FSMContext):
    if str(msg.text).startswith('✅'):
        download = True
    elif str(msg.text).startswith('🛑'):
        download = False
    else:
        return

    if download:
        user = Registry.get_user(msg.chat.id)
        data = await state.get_data()
        mime_type = 'video/mp4'
        if user.isregionuser():
            video_name = data['video_name']
        else:
            video_name = user.state_number

        if 'mime_type' in data:
            mime_type = data['mime_type']


        video_path = str(data['video_path'])
        files_in_city_dir = show_files_in_directory(user.city.dir_id)
        month_year_dir = get_month_year()
        for file in files_in_city_dir:
            if file['name'] == month_year_dir:
                parents_upload_dir_id = file['id']
                break
        else:
            parents_upload_dir_id = create_folder(month_year_dir, user.city.dir_id)

        files = show_files_in_directory(parents_upload_dir_id)
        video_extension = video_path.split('.')[-1]
        i = 1

        file_exists = True
        new_video_name = video_name

        while file_exists:
            for file in files:
                if file['name'] == new_video_name + '.' + video_extension:
                    new_video_name = video_name + f'({str(i)})'
                    i += 1
                    break
            else:
                file_exists = False
                break

        if new_video_name != video_name:
            file_id = upload_video(video_path, new_video_name + '.' + video_extension, parents_upload_dir_id, mime_type)
        else:
            file_id = upload_video(video_path, video_name + '.' + video_extension, parents_upload_dir_id, mime_type)

        os.remove(video_path)

        if not user.isregionuser():
            file_link = "https://drive.google.com/file/d/{0}/view".format(file_id)
            reg_users_list = user.select_regional_users()
            reg_users = []
            if reg_users_list:
                for user_f in reg_users_list:
                    reg_users.append(Registry.get_user(user_f[1]))

            if reg_users:
                text = 'Загружен осмотр! \nUsername: @{0} | Гос. номер: {1}\nСсылка на осмотр - '.format(user.username, user.state_number) + file_link
                kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Заблокировать', callback_data=f'block_driver:{user.chat_id}'))
                for user_f in reg_users:
                    await bot.send_message(user_f.chat_id, text, reply_markup=kb)

        await state.finish()
        kb = start_keyboard(msg.chat.id)
        text = '✅✅ Осмотр отправлен ✅✅'
        await msg.answer(text, reply_markup=kb)
    else:
        text = 'Загрузите видео или снимите новое'
        cancel_kb = cancel_keyboard()
        await msg.answer(text, reply_markup=cancel_kb)
        await UploadReview.previous()

# ---------------- Обработчики для новых пользователей

# Выбор города


@dp.message_handler(Text(startswith="👉", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def set_city_start(msg: types.Message, state: FSMContext):
    keyboard = city_inline_keyboard()
    await StateCity.wait_for_city.set()
    text = 'Выберите ваш город'
    cancel_text = cancel_text_func()
    cancel_kb = cancel_keyboard()
    mes1 = await bot.send_message(msg.chat.id, text, reply_markup=keyboard)
    mes2 = await bot.send_message(msg.chat.id, cancel_text, reply_markup=cancel_kb)
    await state.update_data(msg_city=mes1.message_id)
    await state.update_data(msg_cancel=mes2.message_id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('city_id'), state=StateCity.wait_for_city)
async def processing_city(callback_query: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    city_id = int(str(callback_query.data).replace('city_id:', ''))
    await bot.delete_message(callback_query.message.chat.id, state_data['msg_city'])
    await bot.delete_message(callback_query.message.chat.id, state_data['msg_cancel'])
    loader.add_user(callback_query.message.chat.id, callback_query.message.chat.username, city_id)
    await state.finish()
    message = start_text(callback_query.message.chat.id)
    keyboard = start_keyboard(callback_query.message.chat.id)
    await bot.send_message(callback_query.message.chat.id, message, reply_markup=keyboard)


# ---------------- Обработчики для водителей

# Указать гос. номер
@dp.message_handler(Text(startswith="🛠", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def start_set_state_number(msg: types.Message):
    if User.validate_driver(msg.chat.id):
        cancel_kb = cancel_keyboard()
        text = "Введите гос. номер авто в формате AA1111BB, буквы должны быть латинскими.\nДля отмены нажмите на кнопку или введите /cancel"
        await StateNumber.wait_for_state_number.set()
        await msg.answer(text, reply_markup=cancel_kb)


# Изменить гос. номер
@dp.message_handler(Text(startswith="🔂", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def start_set_state_number(msg: types.Message):
    if User.validate_driver(msg.chat.id):
        cancel_kb = cancel_keyboard()
        text = "Введите гос. номер авто в формате AA1111BB, буквы должны быть латинскими.\nДля отмены нажмите на кнопку или введите /cancel"
        await StateNumber.wait_for_state_number.set()
        await msg.answer(text, reply_markup=cancel_kb)


@dp.message_handler(state=StateNumber.wait_for_state_number, content_types=types.ContentTypes.TEXT)
async def processing_state_number(msg: types.Message, state: FSMContext):
    state_number = User.validate_state_number(msg.text)
    if state_number:
        text = start_text(msg.chat.id)
        kb = start_keyboard(msg.chat.id)
        user = Registry.get_user(msg.chat.id)
        user.change_state_number(state_number)
        await msg.answer('Гос. номер изменен')
        await state.finish()
        await msg.answer(text, reply_markup=kb)
    else:
        text = "Неверный формат гос. номера. Введите номер заново или нажмите 'Отмена'"
        await msg.answer(text)


# Изменить город
@dp.message_handler(Text(startswith="↪", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def start_change_city(msg: types.Message, state: FSMContext):
    if User.validate_driver(msg.chat.id):
        text = 'Выберите город'
        keyboard = city_inline_keyboard()
        cancel_text = cancel_text_func()
        cancel_kb = cancel_keyboard()
        await StateCity.wait_for_change_city.set()
        mes1 = await bot.send_message(msg.chat.id, text, reply_markup=keyboard)
        mes2 = await bot.send_message(msg.chat.id, cancel_text, reply_markup=cancel_kb)
        await state.update_data(msg_city=mes1.message_id)
        await state.update_data(msg_cancel=mes2.message_id)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('city_id'), state=StateCity.wait_for_change_city)
async def processing_city(callback_query: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    city_id = int(str(callback_query.data).replace('city_id:', ''))
    await bot.delete_message(callback_query.message.chat.id, state_data['msg_city'])
    await bot.delete_message(callback_query.message.chat.id, state_data['msg_cancel'])
    user = Registry.get_user(callback_query.message.chat.id)
    user.change_city(city_id)
    await state.finish()
    message = start_text(callback_query.message.chat.id)
    keyboard = start_keyboard(callback_query.message.chat.id)
    await bot.send_message(callback_query.message.chat.id, message, reply_markup=keyboard)


# ---------------- Обработчики для региональных аккаунтов

@dp.message_handler(Text(startswith="👿", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def show_blocked_drivers(msg: types.Message):
    user = Registry.get_user(msg.chat.id)
    if user.isregionuser():
        for text, kb in get_blocked_drivers_kb_and_text(user):
            await msg.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('block_driver'))
async def unblock_driver(callback_query: types.CallbackQuery):
    user = Registry.get_user(callback_query.message.chat.id)
    if user.isregionuser():
        driver = Registry.get_user(str(callback_query.data).replace('block_driver:', ''))
        driver.change_block(True)
        await callback_query.message.edit_reply_markup(types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Разблокировать', callback_data=f'unblock_driver:{driver.chat_id}')))


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('unblock_driver'))
async def unblock_driver(callback_query: types.CallbackQuery):
    user = Registry.get_user(callback_query.message.chat.id)
    if user.isregionuser():
        driver = Registry.get_user(str(callback_query.data).replace('unblock_driver:', ''))
        driver.change_block(False)
        await callback_query.message.edit_reply_markup(types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Заблокировать', callback_data=f'block_driver:{driver.chat_id}')))


# ---------------- Обработчики для администраторов

# Добавить город
@dp.message_handler(Text(startswith="🌆", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def add_city_start(msg: types.Message, state: FSMContext):
    user = Registry.get_user(msg.chat.id)
    if user.isadmin():
        await AddCity.wait_for_city_name.set()
        text = 'Введите название города(не будет отображатся водителю)'
        cancel_kb = cancel_keyboard()
        await msg.answer(text, reply_markup=cancel_kb)


@dp.message_handler(state=AddCity.wait_for_city_name, content_types=types.ContentTypes.TEXT)
async def add_city_name(msg: types.Message, state: FSMContext):
    city_name = str(msg.text).strip()
    await state.update_data(city_name=city_name)
    await AddCity.wait_for_city_ukr_name.set()
    text = 'Введите название города на украинском(будет отображатся водителю)'
    await msg.answer(text)


@dp.message_handler(state=AddCity.wait_for_city_ukr_name, content_types=types.ContentTypes.TEXT)
async def add_city_ukr_name(msg: types.Message, state: FSMContext):
    city_ukr_name = str(msg.text).strip()
    await state.update_data(city_ukr_name=city_ukr_name)
    await AddCity.wait_for_city_id.set()
    text = 'Введите id папки этого города'
    await msg.answer(text)


@dp.message_handler(state=AddCity.wait_for_city_id, content_types=types.ContentTypes.TEXT)
async def add_city_id(msg: types.Message, state: FSMContext):
    city_id = str(msg.text).strip()
    data = await state.get_data()
    try:
        City.validate_dirid(city_id)
    except AssertionError:
        text = "Папки для города {0} с id {1} не существует!! ❌".format(data['city_name'], city_id)
        await msg.answer(text)
        return
    else:
        if City.selectcitybyid(city_id):
            await msg.answer('Город уже существует', reply_markup=start_keyboard(msg.chat.id))
            await state.finish()
        else:
            loader.add_city(data['city_name'], data['city_ukr_name'], city_id)
            text = 'Город {0} с id {1} успешно добавлен!! ✅'.format(data['city_name'], city_id)
            kb = start_keyboard(msg.chat.id)
            await msg.answer(text, reply_markup=kb)
            await state.finish()


# Показать все города
@dp.message_handler(Text(startswith="👁", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def show_cities(msg: types.Message):
    user = Registry.get_user(msg.chat.id)
    if user.isadmin():
        text = 'Список городов'
        kb = city_inline_keyboard(True)
        await msg.answer(text, reply_markup=kb)


# Изменить город
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('show_city_id'))
async def change_city(callback_query: types.CallbackQuery):
    city_id = int(str(callback_query.data).replace('show_city_id:', ''))
    kb = change_city_inline_keyboard(city_id)
    await callback_query.message.edit_reply_markup(reply_markup=kb)


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('selected_show_city_id'))
async def change_city(callback_query: types.CallbackQuery):
    kb = city_inline_keyboard(True)
    await callback_query.message.edit_reply_markup(reply_markup=kb)


# Изменить название города
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('change_city_name'))
async def change_city_name_start(callback_query: types.CallbackQuery, state: FSMContext):
    kb = city_inline_keyboard(True)
    await callback_query.message.edit_reply_markup(reply_markup=kb)
    city_id = int(str(callback_query.data).replace('change_city_name:', ''))
    await ChangeCity.wait_for_city_name.set()
    await state.update_data(city_id=city_id)
    text = 'Введите новое название города(не отображается у водителей)'
    cancel_kb = cancel_keyboard()
    await callback_query.message.answer(text, reply_markup=cancel_kb)


@dp.message_handler(state=ChangeCity.wait_for_city_name, content_types=types.ContentTypes.TEXT)
async def change_city_name_processing(msg: types.Message, state: FSMContext):
    city_name = str(msg.text).strip()
    city_id = await state.get_data()
    city_id = int(city_id['city_id'])
    kb = start_keyboard(msg.chat.id)
    text = 'Название города изменено на ' + city_name
    city = Registry.get_city(city_id)
    if city.change_name(city_name):
        await msg.answer(text, reply_markup=kb)
    else:
        await msg.answer('Something wrong with change city')

    await state.finish()


# Изменить украинское название города
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('change_city_ukr_name'))
async def change_city_ukr_name_start(callback_query: types.CallbackQuery, state: FSMContext):
    kb = city_inline_keyboard(True)
    await callback_query.message.edit_reply_markup(reply_markup=kb)
    city_id = int(str(callback_query.data).replace('change_city_ukr_name:', ''))
    await ChangeCity.wait_for_city_ukr_name.set()
    await state.update_data(city_id=city_id)
    text = 'Введите новое название города на украинском(отображается у водителей)\n Текущее украинское название: ' + Registry.get_city(city_id).ukr_name
    cancel_kb = cancel_keyboard()
    await callback_query.message.answer(text, reply_markup=cancel_kb)


@dp.message_handler(state=ChangeCity.wait_for_city_ukr_name, content_types=types.ContentTypes.TEXT)
async def change_city_ukr_name_processing(msg: types.Message, state: FSMContext):
    city_ukr_name = str(msg.text).strip()
    city_id = await state.get_data()
    city_id = int(city_id['city_id'])
    kb = start_keyboard(msg.chat.id)
    text = 'Украинское название города изменено на ' + city_ukr_name
    city = Registry.get_city(city_id)
    if city.change_ukrname(city_ukr_name):
        await msg.answer(text, reply_markup=kb)
    else:
        await msg.answer('Something wrong with change city')

    await state.finish()


# Изменить id папки города
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('change_city_dir_id'))
async def change_city_dir_id_start(callback_query: types.CallbackQuery, state: FSMContext):
    kb = city_inline_keyboard(True)
    await callback_query.message.edit_reply_markup(reply_markup=kb)
    city_id = int(str(callback_query.data).replace('change_city_dir_id:', ''))
    await ChangeCity.wait_for_city_dir_id.set()
    await state.update_data(city_id=city_id)
    text = 'Введите новый id папки города'
    cancel_kb = cancel_keyboard()
    await callback_query.message.answer(text, reply_markup=cancel_kb)


@dp.message_handler(state=ChangeCity.wait_for_city_dir_id, content_types=types.ContentTypes.TEXT)
async def change_city_dir_id_processing(msg: types.Message, state: FSMContext):
    city_dir_id = str(msg.text).strip()
    city_id = await state.get_data()
    city_id = int(city_id['city_id'])
    try:
        City.validate_dirid(city_dir_id)
    except AssertionError:
        kb = start_keyboard(msg.chat.id)
        await msg.answer('Такого id не существует на гугл диске', reply_markup=kb)
        await state.finish()
    else:
        kb = start_keyboard(msg.chat.id)
        text = 'id папки города изменено на ' + city_dir_id
        city = Registry.get_city(city_id)
        city.change_dir_id(city_dir_id)
        await state.finish()
        await msg.answer(text, reply_markup=kb)


# Добавить администратора
@dp.message_handler(Text(startswith="🧔", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def add_admin_start(msg: types.Message):
    user = Registry.get_user(msg.chat.id)
    if user:
        if user.isadmin():
            cancel_kb = cancel_keyboard()
            text = 'Введите chat id пользователя'
            await AddAdmin.wait_for_chat_id.set()
            await msg.answer(text, reply_markup=cancel_kb)


@dp.message_handler(state=AddAdmin.wait_for_chat_id, content_types=types.ContentTypes.TEXT)
async def add_admin_proccesing_chat_id(msg: types.Message, state: FSMContext):
    chat_id = int(str(msg.text).strip())
    await state.update_data(chat_id=chat_id)
    text = 'Введите username из телеграмма для нового администратора(без собаки @)'
    await AddAdmin.next()
    await msg.answer(text)


@dp.message_handler(state=AddAdmin.wait_for_username, content_types=types.ContentTypes.TEXT)
async def add_admin_proccesing_username(msg: types.Message, state: FSMContext):
    username = str(msg.text).strip()
    chat_id = await state.get_data()
    chat_id = int(chat_id['chat_id'])
    user = Registry.get_user(chat_id)
    if user:
        user.change_permission(3)
    else:
        loader.add_user(chat_id=chat_id, username=username, permission_level=3)

    await state.finish()
    text = 'Администратор добавлен'
    kb = start_keyboard(msg.chat.id)
    await msg.answer(text, reply_markup=kb)


# Добавить региональный аккаунт
@dp.message_handler(Text(startswith="🐕", ignore_case=True), content_types=types.ContentTypes.TEXT)
async def add_region_acc_start(msg: types.Message):
    user = Registry.get_user(msg.chat.id)
    if user:
        if user.isadmin():
            await AddRegionalAcc.wait_for_chat_id.set()
            text = 'Введите чат-ид регионального аккаунта'
            await msg.answer(text)
            cancel_kb = cancel_keyboard()
            cancel_text = cancel_text_func()
            await msg.answer(cancel_text, reply_markup=cancel_kb)


@dp.message_handler(state=AddRegionalAcc.wait_for_chat_id, content_types=types.ContentTypes.TEXT)
async def add_regiona_acc_processing(msg: types.Message, state: FSMContext):
    reg_acc_chat_id = str(msg.text).strip()
    user = Registry.get_user(reg_acc_chat_id)
    if user:
        user.change_permission(2)
        await state.finish()
        kb = start_keyboard(msg.chat.id)
        text = 'Пользователь добавлен как региональный аккаунт'
        await msg.answer(text, reply_markup=kb)
    else:
        await msg.answer('Данного пользователя нет в базе. Пользователю необходимо зайтив бота и выбрать город')
        return

# ---------------- Обработчики для superadmin


if __name__ == '__main__':
    executor.start_polling(dp)
