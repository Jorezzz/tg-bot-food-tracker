from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from auth.utils import permission_allowed


async def main_keyboard(user_id, is_persistent=True):
    kb_list = [
        [KeyboardButton(text="Статус за день"), KeyboardButton(text="Настройки")],
        [KeyboardButton(text="Помощь")],
    ]
    is_allowed = await permission_allowed(user_id, 1)
    if not is_allowed:
        kb_list = [[KeyboardButton(text="Регистрация")]] + kb_list
    return ReplyKeyboardMarkup(
        is_persistent=is_persistent,
        keyboard=kb_list,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Воспользуйтесь меню:",
    )


async def settings_keyboard():
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
