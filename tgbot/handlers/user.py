import logging
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from tgbot.keyboards.callback_data import race_callback
from tgbot.models.sqlitedb import (
    get_or_add_user,
    get_running_races,
    set_race_followed,
    find_entry,
)
from tgbot.keyboards.inline import races_kb


async def user_start(message: Message):
    races = await get_running_races()
    kb = races_kb(races, "view")
    await get_or_add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Привет, {message.from_user.username}!\n\n \
Для начала выбери мероприятие:",
        reply_markup=kb,
    )


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["start"], state="*")


async def user_follow_race(call: CallbackQuery, callback_data: dict):
    await set_race_followed(call.from_user.id, callback_data.get("id"))
    await call.answer()
    race_title = callback_data.get("title")
    race_date = callback_data.get("date")
    await call.message.answer(
        f"Отлично, ты выбрал мероприятие '{race_title} {race_date}'\n"
        "Теперь ты можешь следующее:"
        "1. Искать участника/команду по номеру манишки или по фамилии"
    )


def register_user_follow_race(dp: Dispatcher):
    dp.register_callback_query_handler(
        user_follow_race, race_callback.filter(action="view")
    )


async def search_results(message: Message):
    user = await get_or_add_user(message.from_user.id, message.from_user.username)

    answer_message = await find_entry(user[1], message.text)
    if len(answer_message) == 0:
        await message.answer(
            "Атлета/команды с таким номером нет. Попробуй другой номер"
        )
    else:
        for entry in answer_message:
            await message.answer(
                f"Стартовый номер: {entry.dorsal}\n\
{entry.name} {entry.surname}\n\
Чистое время: {entry.time_real}\n\
Категория: {entry.category}"
            )


def redister_searh_results(dp: Dispatcher):
    dp.register_message_handler(search_results)
