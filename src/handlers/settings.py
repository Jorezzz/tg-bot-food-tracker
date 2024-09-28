from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.functions import update_user, swap_time


class EnergyLimitForm(StatesGroup):
    energy_limit = State()


class DayFinishForm(StatesGroup):
    day_finish = State()


settings_router = Router()


@settings_router.message(F.text == "/update_finish_day")
async def start_updating_finish_day(message: Message, state: FSMContext):
    await state.set_state(DayFinishForm.day_finish)
    await message.reply("Укажите новое время окончания дня в формате час.минута")


@settings_router.message(DayFinishForm.day_finish)
async def process_finish_day(message: Message, state: FSMContext):
    await state.clear()
    try:
        await swap_time(
            message.from_user.id,
            str(int(message.text.split(".")[0])),
            str(int(message.text.split(".")[1])),
        )
        await message.answer(text="Время окончания дня измененно")
    except ValueError:
        await message.answer(text="Неверный формат ввода")


@settings_router.message(F.text == "/update_daily_limit")
async def start_updating_daily_limit(message: Message, state: FSMContext):
    await state.set_state(EnergyLimitForm.energy_limit)
    await message.reply("Укажите новый лимит каллорий")


@settings_router.message(EnergyLimitForm.energy_limit)
async def process_energy_limit(message: Message, state: FSMContext):
    await state.clear()
    try:
        await update_user(message.from_user.id, {"energy_limit": int(message.text)})
        await message.answer(text="Дневной лимит изменён")
    except ValueError:
        await message.answer(text="Неверный формат ввода")
