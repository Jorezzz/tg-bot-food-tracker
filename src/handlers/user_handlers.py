from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from create_bot import bot, dp, OPENAI_TOKEN, logger
import io
from utils import encode_image, form_output
from model import get_chatgpt_description
from db.functions import register_user, add_daily_energy, get_user, update_user, pg_log_message, swap_time


class EnergyLimitForm(StatesGroup):
    energy_limit = State()


class DayFinishForm(StatesGroup):
    day_finish = State()


user_router = Router()


@user_router.message(F.text == '/start')
async def start(message: Message):
    await message.answer(text='Перед использованием нужно зарегистрироваться')


@user_router.message(F.text == '/register')
async def init_user(message: Message):
    try:
        await register_user(message)
        await message.answer(text='Successfully registered')
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")


@user_router.message(F.text == '/daily_total')
async def get_daily_total(message: Message):
    try:
        user_data = await get_user(message.from_user.id)
        await message.answer(text=f"Дневной лимит каллорий {user_data['current_energy']} из {user_data['energy_limit']}")
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")


@user_router.message(F.text == '/update_finish_day')
async def start_updating_finish_day(message, state: FSMContext):
    await state.set_state(DayFinishForm.day_finish)
    await message.reply("Укажите новое время окончания дня в формате час.минута")


@user_router.message(DayFinishForm.day_finish)
async def process_finish_day(message, state: FSMContext):
    await state.clear()
    try:
        await swap_time(
            message.from_user.id, 
            str(int(message.text.split('.')[0])), 
            str(int(message.text.split('.')[1]))
        )
        # hour = int(message.text.split('.')[0])
        # minute = int(message.text.split('.')[1])
        # await update_user(
        #     message.from_user.id, 
        #     {
        #         'end_hour': hour,
        #         'end_minute': minute,
        #     }
        # )
        await message.answer(text='Время окончания дня измененно')
    except ValueError:
        await message.answer(text="Неверный формат ввода")


@user_router.message(F.text == '/update_daily_limit')
async def start_updating_daily_limit(message, state: FSMContext):
    """Conversation entrypoint"""
    # Set state
    await state.set_state(EnergyLimitForm.energy_limit)
    await message.reply("Укажите новый лимит каллорий")


@user_router.message(EnergyLimitForm.energy_limit)
async def process_energy_limit(message, state: FSMContext):
    # Finish our conversation
    await state.clear()
    try:
        await update_user(message.from_user.id, {'energy_limit': int(message.text)})
        await message.answer(text='Дневной лимит изменён')
    except ValueError:
        await message.answer(text="Неверный формат ввода")


@user_router.message(F.photo)
async def parse_photo(message: Message):
    file_in_io = io.BytesIO()
    file = await bot.get_file(message.photo[-1].file_id)
    await bot.download_file(file.file_path, file_in_io)
    b64_photo = encode_image(file_in_io.read())
    response = await get_chatgpt_description(
        b64_photo, 
        OPENAI_TOKEN, 
        logger
    )
    model_output = eval(response['content'])
    output = form_output(model_output)
    await pg_log_message(message, model_output, b64_photo)
    await update_user(message.from_user.id, {'last_image_message_id': message.message_id})

    await add_daily_energy(message.from_user.id, output[1])
    await message.answer(text=output[0])