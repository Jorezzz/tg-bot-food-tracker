from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import logger


def main_keyboard(is_persistent=True):
    kb_list = [
        [KeyboardButton(text="Статус за день"), KeyboardButton(text="Настройки")],
        [KeyboardButton(text="Помощь")],
    ]
    # is_allowed = await permission_allowed(user_id, 1)
    # if not is_allowed:
    #     kb_list = [[KeyboardButton(text="Регистрация")]] + kb_list
    return ReplyKeyboardMarkup(
        is_persistent=is_persistent,
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Воспользуйтесь меню:",
    )


def settings_keyboard():
    kb_list = [
        [KeyboardButton(text="Изменить дневной лимит")],
        [KeyboardButton(text="Изменить время окончания дня")],
        [KeyboardButton(text="Назад")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Воспользуйтесь меню:",
    )


def dishes_keyboard(user_id, message_id, dishes_and_drinks):
    counter = 0
    inline_kb_list = []
    data = []
    for dd in dishes_and_drinks:
        data.append(
            InlineKeyboardButton(
                text=dd.get("drink_name") or dd.get("dish_name"),
                callback_data="options_"
                + str(message_id)
                + "_"
                + str(dd.get("drink_name") or dd.get("dish_name")),
            )
        )
        counter += 1
        if counter == 2:
            counter = 0
            inline_kb_list.append(data)
            data = []
    if len(data) > 0:
        inline_kb_list.append(data)
    logger.info(f"{inline_kb_list}")
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def remove_or_edit_keyboard(user_id, message_id, dish_name):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить",
                    callback_data="delete_" + str(message_id) + "_" + dish_name,
                ),
                InlineKeyboardButton(
                    text="Изменить вес",
                    callback_data="edit_" + str(message_id) + "_" + dish_name,
                ),
            ]
        ]
    )
