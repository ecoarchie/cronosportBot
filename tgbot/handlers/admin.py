from logging import warning
from aiogram import Dispatcher
from aiogram.types import Message, message
from aiogram.types.callback_query import CallbackQuery
from tgbot.models.sqlitedb import (
    add_race,
    get_all_races,
    delete_race,
    get_running_races,
)
from datetime import datetime
from tgbot.keyboards.inline import races_kb
from tgbot.keyboards.callback_data import race_callback


async def admin_start(message: Message):
    await message.reply("Hello, admin!")


def register_admin(dp: Dispatcher):
    dp.register_message_handler(
        admin_start, commands=["start"], state="*", is_admin=True
    )


""" добавление мероприятия в базу данных """
## парсинг сообщения формата "race_id, race_title, race_date"
def _parse_race_messsage(raw_message: str):
    command, race_id, race_title, race_date_str = raw_message.split(",")
    race_date = datetime.strptime(race_date_str, "%d.%m.%Y")
    return {"race_id": race_id, "race_title": race_title, "race_date": race_date}


async def add_race_to_db(message: Message):
    race_info = _parse_race_messsage(message.text)
    print(race_info)
    answer_message = await add_race(
        race_id=race_info["race_id"],
        race_title=race_info["race_title"],
        race_date=race_info["race_date"],
    )
    races = await get_running_races()
    kb = races_kb(races, "view")
    await message.answer(answer_message, reply_markup=kb)


def register_add_race_info(dp: Dispatcher):
    dp.register_message_handler(add_race_to_db, commands=["add_race"])


"""Получение списка всех мероприятий и удаление из данного списка"""
# получение списка мероприятий и вывод клавиатуры с названиями мероприятий
# клавиатура создается и в нее передается параметр для callback data со значением "delete"
# по данному значению будет фильтроваться выбор функции при регистрации хэндлера с функцией удаления
async def get_races_list(message: Message):
    races = await get_all_races()
    kb = races_kb(races, "delete")
    await message.answer(
        "Нажми на название Мероприятия для его удаления из БД",
        reply_markup=kb,
    )


def register_get_races_list(dp: Dispatcher):
    dp.register_message_handler(get_races_list, commands=["del_races"], state="*")


# удаление мероприятия по нажатию кнопки с его названием,
async def delete_race_from_db(call: CallbackQuery, callback_data: dict):
    race_id = callback_data.get("id")
    answer_message = await delete_race(race_id)
    races = await get_all_races()
    kb = races_kb(races, "delete")
    await call.message.answer(answer_message, reply_markup=kb)


def register_delete_race_from_db(dp: Dispatcher):
    dp.register_callback_query_handler(
        delete_race_from_db, race_callback.filter(action="delete")
    )
