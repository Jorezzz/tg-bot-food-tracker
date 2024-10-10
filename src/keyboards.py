from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from utils import hash
from config import balance_prices, PHOTO_DESCRIPTION_PRICE


def main_keyboard(is_persistent=True):
    kb_list = [
        [KeyboardButton(text="Статус"), KeyboardButton(text="Настройки")],
        [
            KeyboardButton(text="Пополнить баланс"),
            KeyboardButton(text="Ввести промокод"),
        ],
        [KeyboardButton(text="Помощь")],
    ]
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


def dishes_keyboard(message_id, dishes_and_drinks):
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
                + str(hash((dd.get("drink_name")) or dd.get("dish_name"))),
            )
        )
        counter += 1
        if counter == 2:
            counter = 0
            inline_kb_list.append(data)
            data = []
    if len(data) > 0:
        inline_kb_list.append(data)
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def remove_or_edit_keyboard(message_id, dish_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить",
                    callback_data="delete_" + str(message_id) + "_" + str(dish_id),
                ),
                InlineKeyboardButton(
                    text="Изменить вес",
                    callback_data="edit_" + str(message_id) + "_" + str(dish_id),
                ),
            ]
        ]
    )


def get_inline_button_by_packet(packet):
    return InlineKeyboardButton(
        text=f"{balance_prices[packet]} рублей ({packet} фото)",
        callback_data=f"pay_{packet*PHOTO_DESCRIPTION_PRICE}_{balance_prices[packet]}",
    )


def payment_size_keyboard():
    kb_list = [
        [
            get_inline_button_by_packet(20),
            get_inline_button_by_packet(50),
        ],
        [
            get_inline_button_by_packet(100),
            get_inline_button_by_packet(300),
        ],
        [InlineKeyboardButton(text="Назад", callback_data="cancel_payment")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)


def payment_keyboard(price):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Оплатить {price} рублей",
                    pay=True,
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Отменить оплату", callback_data="cancel_payment"
                )
            ],
        ],
    )
