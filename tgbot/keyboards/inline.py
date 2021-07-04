from aiogram.types import InlineKeyboardButton
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from tgbot.keyboards.callback_data import race_callback


def races_kb(races, action):

    races_buttons = []

    for race in races:
        races_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{race[1]} {race[2]}",
                    callback_data=race_callback.new(
                        id=race[0], title=race[1], date=race[2], action=action
                    ),
                )
            ]
        )

    race_choice = InlineKeyboardMarkup(row_width=1, inline_keyboard=races_buttons)
    return race_choice
