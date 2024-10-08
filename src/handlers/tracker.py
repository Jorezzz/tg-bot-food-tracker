from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from create_bot import bot
from config import (
    logger,
    PHOTO_DESCRIPTION_PRICE,
    REMAINING_ENERGY_SUGGESTION_PRICE,
)
from auth.utils import check_if_valid_balance
import io
from utils import encode_image
from model import (
    get_chatgpt_photo_description,
    get_chatgpt_remaining_energy_suggestion,
    form_output,
)
from db.functions import (
    add_meal_energy,
    get_user,
    pg_log_message,
    remove_dish_from_user_day,
    update_dish_quantity,
    get_dish_by_id,
    update_user_balance,
)
from aiogram.utils.chat_action import ChatActionSender
from keyboards import main_keyboard, dishes_keyboard, remove_or_edit_keyboard


class NewDishQuantityForm(StatesGroup):
    quantity = State()
    user_id = State()
    message_id = State()
    dish_id = State()


tracker_router = Router()


@tracker_router.message(F.text.contains("Статус"))
@tracker_router.message(F.text == "/daily_total")
async def get_daily_total(message: Message):
    user_id = message.from_user.id
    try:
        user = await get_user(user_id)
        await message.answer(
            text=f"Дневной лимит калорий: {user['current_energy']} из {user['energy_limit']}\n\nБаланс: {user.get('balance', 0)} ⭐️"
        )
        # is_valid_balance = await check_if_valid_balance(
        #     user, REMAINING_ENERGY_SUGGESTION_PRICE
        # )
        # if is_valid_balance:
        suggestion = await get_chatgpt_remaining_energy_suggestion(
            round(
                user["energy_limit"] - user["current_energy"],
                -1,
            ),
        )
        await message.answer(text=suggestion, reply_markup=main_keyboard())
        # await update_user_balance(
        #     user_id, int(user["balance"]) - REMAINING_ENERGY_SUGGESTION_PRICE
        # )
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Что-то пошло не так", reply_markup=main_keyboard())


@tracker_router.message(F.photo)
async def parse_photo(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    is_valid_balance = await check_if_valid_balance(user, PHOTO_DESCRIPTION_PRICE)
    if not is_valid_balance:
        await message.answer(
            "Недостаточно средств, пополни баланс ⭐️ нажав 'Пополнить баланс'",
            reply_markup=main_keyboard(),
        )
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
        await update_user_balance(user_id, user["balance"] - PHOTO_DESCRIPTION_PRICE)
        if user["balance"] - PHOTO_DESCRIPTION_PRICE < 1:
            await message.answer(
                text="Ой! Кажется на балансе закончились ⭐️. Чтобы пополнить нажми 'Пополнить баланс'"
            )


@tracker_router.callback_query(F.data.startswith("options_"))
async def options_dishes(call: CallbackQuery):
    await call.answer()
    message_id = call.data.split("_")[1]
    dish_id = "".join(call.data.split("_")[2:])
    dish_params = await get_dish_by_id(call.from_user.id, int(message_id), int(dish_id))
    await call.message.answer(
        f"Выбери действие c {dish_params['name']}",
        reply_markup=remove_or_edit_keyboard(message_id, dish_id),
    )


@tracker_router.callback_query(F.data.startswith("delete_"))
async def options_dishes_delete(call: CallbackQuery):
    await call.answer()
    message_id = int(call.data.split("_")[1])
    dish_id = "".join(call.data.split("_")[2:])
    await remove_dish_from_user_day(call.from_user.id, int(message_id), int(dish_id))
    await call.message.answer(f"Блюдо успешно удалено")


@tracker_router.callback_query(F.data.startswith("edit_"))
async def options_dishes_edit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user_id = call.from_user.id
    message_id = call.data.split("_")[1]
    dish_id = "".join(call.data.split("_")[2:])
    await state.update_data(user_id=user_id)
    await state.update_data(message_id=message_id)
    await state.update_data(dish_id=dish_id)
    await state.set_state(NewDishQuantityForm.quantity)
    await call.message.answer("Укажи новый вес блюда в граммах (миллилитрах)")


@tracker_router.message(NewDishQuantityForm.quantity)
async def edit_dish(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    try:
        await update_dish_quantity(
            int(data.get("user_id")),
            int(data.get("message_id")),
            int(data.get("dish_id")),
            int(message.text),
        )
        await message.answer(text="Вес изменён")
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Неверный формат ввода")
