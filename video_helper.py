from telethon import TelegramClient
import asyncio
import shutil
from pathlib import *
from init import files_dir
from core.Db import Db
from init import log_file_video
from core.Logger import Logger

database = Db()

cursor = database.cursor
conn = database.conn
log = Logger.get_instance(log_file_video).info


def get_last_msg_id():
    sql = "select value from settings where name='msg_id'"
    cursor.execute(sql)
    return int(cursor.fetchone()[0])


def set_msg_id(msg_id: int):
    sql = "update settings set value=? where name='msg_id'"
    cursor.execute(sql, (msg_id,))
    conn.commit()


min_id = get_last_msg_id()


entity = 'UklonVideoHelper'
api_id = 7856551
api_hash = '06a229e18c54aadfcdd6af18be38ed3e'
phone = '+380930224576'


async def main():
    global min_id
    client = TelegramClient(entity, api_id, api_hash)
    await client.connect()
    if not (await client.is_user_authorized()):
        # client.send_code_request(phone) #при первом запуске - раскомментить, после авторизации для избежания FloodWait - закомментить
        await client.sign_in(phone, input('Enter code: '))
    await client.start()

    while True:
        messages = await client.get_messages('mrplbrand_bot', min_id=min_id)
        if messages:
            mess = messages[0]
            try:
                message_id = mess.id
                min_id = int(message_id)
                set_msg_id(min_id)
                file = await client.download_media(message=mess, file=str(mess.media.document.size))
                shutil.move(file, files_dir / file)
            except Exception as e:
                log(e)
                log(mess)

        await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
