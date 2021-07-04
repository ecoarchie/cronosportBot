from aiogram.types import InlineKeyboardButton
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from tgbot.keyboards.callback_data import race_callback

def running_races_kb(races):

    races_buttons = []

    for race in races:
        races_buttons.append([InlineKeyboardButton(text=f"{race[1]} {race[2]}", callback_data=race_callback.new(race_id=race[0], race_title=race[1], race_date=race[2]))])

    race_choice = InlineKeyboardMarkup(row_width=1, inline_keyboard=races_buttons)
    return race_choice