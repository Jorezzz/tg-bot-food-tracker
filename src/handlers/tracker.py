from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from create_bot import bot
from config import logger
from auth.utils import permission_allowed
import io
from utils import encode_image, hash
from model import (
    get_chatgpt_photo_description,
    get_chatgpt_remaining_energy_suggestion,
    form_output,
)
from db.functions import (
    add_meal_energy,
    get_user,
    update_user,
    pg_log_message,
    remove_dish_from_user_day,
    update_dish_quantity,
    get_dish_by_id,
)
from aiogram.utils.chat_action import ChatActionSender
from keyboard import main_keyboard, dishes_keyboard, remove_or_edit_keyboard


class NewDishQuantityForm(StatesGroup):
    quantity = State()
    user_id = State()
    message_id = State()
    dish_id = State()


tracker_router = Router()


@tracker_router.message(F.text.contains("Статус за день"))
@tracker_router.message(F.text == "/daily_total")
async def get_daily_total(message: Message):
    try:
        user_data = await get_user(message.from_user.id)
        await message.answer(
            text=f"Дневной лимит калорий {user_data['current_energy']} из {user_data['energy_limit']}"
        )
        suggestion = await get_chatgpt_remaining_energy_suggestion(
            round(
                int(user_data["energy_limit"]) - int(user_data["current_energy"]), -1
            ),
        )
        await message.answer(text=suggestion, reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured", reply_markup=main_keyboard())


@tracker_router.message(F.photo)
async def parse_photo(message: Message):
    user_id = message.from_user.id
    is_allowed = await permission_allowed(user_id, 1)
    if not is_allowed:
        await message.answer("Недостаточно прав", reply_markup=main_keyboard())
        return None

    async with ChatActionSender.typing(bot=bot, chat_id=user_id):
        file_in_io = io.BytesIO()
        file = await bot.get_file(message.photo[-1].file_id)
        await bot.download_file(file.file_path, file_in_io)
        b64_photo = encode_image(file_in_io.read())

        text = None  # message.caption
        if text is not None:
            response = await get_chatgpt_photo_description(b64_photo, text)
        else:
            response = await get_chatgpt_photo_description(b64_photo)
        model_output = eval(response["content"])
        output = form_output(model_output)
        await pg_log_message(message, model_output, b64_photo)
        await update_user(user_id, {"last_image_message_id": message.message_id})

        await add_meal_energy(
            user_id,
            output["energy_total"],
            output["proteins_total"],
            output["carbohydrates_total"],
            output["fats_total"],
        )
        await message.answer(
            text=output["output_text"],
            reply_markup=dishes_keyboard(
                message.message_id,
                model_output["dishes"] + model_output["drinks"],
            ),
        )


@tracker_router.callback_query(F.data.startswith("options_"))
async def options_dishes(call: CallbackQuery):
    await call.answer()
    message_id = call.data.split("_")[1]
    dish_id = "".join(call.data.split("_")[2:])
    dish_params = await get_dish_by_id(str(call.from_user.id), message_id, dish_id)
    await call.message.answer(
        f"Выберите действие c {dish_params['name']}",
        reply_markup=remove_or_edit_keyboard(message_id, dish_id),
    )


@tracker_router.callback_query(F.data.startswith("delete_"))
async def options_dishes_delete(call: CallbackQuery):
    await call.answer()
    message_id = call.data.split("_")[1]
    dish_id = "".join(call.data.split("_")[2:])
    await remove_dish_from_user_day(str(call.from_user.id), message_id, dish_id)
    await call.message.answer(f"Блюдо успешно удалено")


@tracker_router.callback_query(F.data.startswith("edit_"))
async def options_dishes_edit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user_id = str(call.from_user.id)
    message_id = call.data.split("_")[1]
    dish_id = "".join(call.data.split("_")[2:])
    await state.update_data(user_id=user_id)
    await state.update_data(message_id=message_id)
    await state.update_data(dish_id=dish_id)
    await state.set_state(NewDishQuantityForm.quantity)
    await call.message.answer("Укажите новый вес блюда в граммах (миллилитрах)")


@tracker_router.message(NewDishQuantityForm.quantity)
async def edit_dish(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    try:
        await update_dish_quantity(
            data.get("user_id"),
            data.get("message_id"),
            data.get("dish_id"),
            int(message.text),
        )
        await message.answer(text="Вес изменён")
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Неверный формат ввода")
