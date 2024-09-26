from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from create_bot import bot, OPENAI_TOKEN, logger
import io
from utils import encode_image, form_output
from openai_requests import get_chatgpt_description
from db.functions import register_user, add_daily_energy, get_user, update_user


class EnergyLimitForm(StatesGroup):
    energy_limit = State()


user_router = Router()


@user_router.message(F.text == '/start')
async def init_user(message: Message):
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
async def init_user(message: Message):
    try:
        user_data = await get_user(message.from_user.id)
        await message.answer(text=f"Дневной лимит каллорий {user_data['current_energy']} из {user_data['energy_limit']}")
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")


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
    output = form_output(response)

    await add_daily_energy(message.from_user.id, output[1])
    await message.answer(text=output[0])