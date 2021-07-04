import logging
from aiogram import Dispatcher
from aiogram.dispatcher import filters
from aiogram.types import Message, User
from aiogram.types import callback_query
from aiogram.types.callback_query import CallbackQuery
from aiogram.utils.callback_data import CallbackData
from tgbot.keyboards.callback_data import race_callback
from sqlalchemy.sql.sqltypes import DateTime
from tgbot.models.sqlitedb import (
    get_or_add_user,
    get_running_races,
    set_race_followed,
    find_entry,
)
from tgbot.keyboards.inline import running_races_kb


async def user_start(message: Message):
    races = await get_running_races()
    kb = running_races_kb(races)
    await get_or_add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Привет, {message.from_user.username}!\n\n \
    Для начала выбери мероприятие:",
        reply_markup=kb,
    )


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")


async def user_follow_race(call: CallbackQuery, callback_data: dict):
    await set_race_followed(call.from_user.id, callback_data.get("race_id"))
    await call.answer()
    race_title = callback_data.get("race_title")
    race_date = callback_data.get("race_date")
    await call.message.answer(
        f"Отлично, ты выбрал мероприятие '{race_title} {race_date}'\n"
        "Теперь ты можешь следующее:"
        "1. Искать участника/команду по номеру манишки или по фамилии"
    )


def register_user_follow_race(dp: Dispatcher):
    dp.register_callback_query_handler(user_follow_race, race_callback.filter())


async def search_results(message: Message):
    user = await get_or_add_user(message.from_user.id, message.from_user.username)

    answer_message = await find_entry(user[1], message.text)
    for entry in answer_message:
        await message.answer(entry)


def redister_searh_results(dp: Dispatcher):
    dp.register_message_handler(search_results)
