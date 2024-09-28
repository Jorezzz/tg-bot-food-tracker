from aiogram import Router, F
from aiogram.types import Message
from config import logger, ADMIN_PASSWORD
from db.functions import register_user
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboard import main_keyboard
import hashlib


class AdminPassword(StatesGroup):
    password = State()


start_router = Router()


@start_router.message(F.text == "/start")
async def start(message: Message):
    kb = await main_keyboard(message.from_user.id, is_persistent=False)
    await message.answer(
        text="Перед использованием нужно зарегистрироваться", reply_markup=kb
    )


@start_router.message(F.text.contains("Регистрация"))
@start_router.message(F.text == "/register")
async def init_user(message: Message):
    try:
        await register_user(message)
        kb = await main_keyboard(message.from_user.id)
        await message.answer(text="Successfully registered", reply_markup=kb)
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")


@start_router.message(F.text == "/register_admin")
async def start_updating_daily_limit(message: Message, state: FSMContext):
    await state.set_state(AdminPassword.password)
    await message.reply("Введите пароль администратора")


@start_router.message(AdminPassword.password)
async def process_energy_limit(message: Message, state: FSMContext):
    await state.clear()
    try:
        if (
            hashlib.sha256(str(message.text).encode()).hexdigest()
            == hashlib.sha256(str(ADMIN_PASSWORD).encode()).hexdigest()
        ):
            await register_user(message, role_id=3)
            await message.answer(text="Добро пожаловать, повелитель")
        else:
            raise Exception("Wrong admin password")
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Неверный пароль, уходи")
