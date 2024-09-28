from aiogram import Router, F
from aiogram.types import Message
from create_bot import logger
from db.functions import register_user

start_router = Router()


@start_router.message(F.text == "/start")
async def start(message: Message):
    await message.answer(text="Перед использованием нужно зарегистрироваться")


@start_router.message(F.text == "/register")
async def init_user(message: Message):
    try:
        await register_user(message)
        await message.answer(text="Successfully registered")
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")
