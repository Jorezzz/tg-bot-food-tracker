from aiogram import Router, F
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.chat_action import ChatActionSender
import asyncio
from auth.utils import check_if_valid_balance
from create_bot import bot
from config import (
    logger,
    PHOTO_DESCRIPTION_PRICE,
    REMAINING_ENERGY_SUGGESTION_PRICE,
    TEXT_DESCRIPTION_PRICE,
)
import io
from utils import encode_image
from model import (
    get_chatgpt_photo_description,
    get_chatgpt_remaining_energy_suggestion,
    form_output,
)
from db.users import (
    add_meal_energy,
    get_user,
    pg_log_message,
)
from db.payments import update_user_balance
from db.dishes import (
    remove_dish_from_user_day,
    update_dish_quantity,
    get_dish_by_id,
)
from keyboards import main_keyboard, dishes_keyboard, remove_or_edit_keyboard


class MediaMiddleware(BaseMiddleware):
    def __init__(self, latency=0.01):
        self.medias = {}
        self.latency = latency
        super(MediaMiddleware, self).__init__()

    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.media_group_id:
            try:
                self.medias[event.media_group_id].append(event)
                return
            except KeyError:
                self.medias[event.media_group_id] = [event]
                await asyncio.sleep(self.latency)

                data["media_events"] = self.medias.pop(event.media_group_id)

        return await handler(event, data)


class NewDishQuantityForm(StatesGroup):
    quantity = State()
    user_id = State()
    message_id = State()
    dish_id = State()


tracker_router = Router()
tracker_router.message.middleware(MediaMiddleware())


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


async def apply_ml_photo_message(message, alarm=True):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not check_if_valid_balance(user, PHOTO_DESCRIPTION_PRICE):
        await message.answer(
            "Для дальнейшей работы недостаточно средств, пополни баланс ⭐️ нажав 'Пополнить баланс'",
            reply_markup=main_keyboard(),
        )
        return "Failed"
    await update_user_balance(user_id, user["balance"] - PHOTO_DESCRIPTION_PRICE)

    async with ChatActionSender.typing(bot=bot, chat_id=user_id):
        file_in_io = io.BytesIO()
        file = await bot.get_file(message.photo[-1].file_id)
        await bot.download_file(file.file_path, file_in_io)
        b64_photo = encode_image(file_in_io.read())

        text = message.caption
        if text is not None:
            response = await get_chatgpt_photo_description(b64_photo, text)
        else:
            response = await get_chatgpt_photo_description(b64_photo)
        model_output = eval(response["content"])
        if len(model_output["dishes"] + model_output["drinks"]) == 0:
            await message.answer(
                text="Я не смог ничего распознать. Проверь, что фото сделано без размытия и на нём отчётливо видно блюдо."
            )
            return None
        output = form_output(model_output)
        await pg_log_message(message, model_output, text)

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
        if alarm:
            if user["balance"] - PHOTO_DESCRIPTION_PRICE < 1:
                await message.answer(
                    text="Ой! Кажется на балансе закончились ⭐️. Чтобы пополнить нажми 'Пополнить баланс'"
                )


@tracker_router.message(F.media_group_id != None)
async def parse_photo(message: Message, media_events):
    for i, mess in enumerate(media_events):
        alarm = True
        if len(media_events) > 1:
            if i != len(media_events) - 1:
                alarm = False
        res = await apply_ml_photo_message(mess, alarm=alarm)
        if res == "Failed":
            return None


@tracker_router.message(F.photo)
async def parse_photo(message: Message):
    await apply_ml_photo_message(message)


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


@tracker_router.message(F.text)
async def parse_text(message, alarm=True):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not check_if_valid_balance(user, TEXT_DESCRIPTION_PRICE):
        await message.answer(
            "Для дальнейшей работы недостаточно средств, пополни баланс ⭐️ нажав 'Пополнить баланс'",
            reply_markup=main_keyboard(),
        )
        return "Failed"
    await update_user_balance(user_id, user["balance"] - TEXT_DESCRIPTION_PRICE)

    async with ChatActionSender.typing(bot=bot, chat_id=user_id):
        text = message.text
        response = await get_chatgpt_photo_description(optional_text=text)
        model_output = eval(response["content"])
        if len(model_output["dishes"] + model_output["drinks"]) == 0:
            await message.answer(
                text="Я не смог ничего распознать. Попробуй описать точнее"
            )
            return None
        output = form_output(model_output)
        await pg_log_message(message, model_output, text)

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
        if alarm:
            if user["balance"] - TEXT_DESCRIPTION_PRICE < 1:
                await message.answer(
                    text="Ой! Кажется на балансе закончились ⭐️. Чтобы пополнить нажми 'Пополнить баланс'"
                )
