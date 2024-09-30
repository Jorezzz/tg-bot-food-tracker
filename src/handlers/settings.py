from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.functions import update_user, swap_time, get_pfc_limits_from_callories_limit
from keyboard import settings_keyboard, main_keyboard


class EnergyLimitForm(StatesGroup):
    energy_limit = State()


class DayFinishForm(StatesGroup):
    day_finish = State()


settings_router = Router()


@settings_router.message(F.text.contains("Настройки"))
async def open_settings_menu(message: Message):
    kb = await settings_keyboard()
    await message.reply("Выберите настройку", reply_markup=kb)


@settings_router.message(F.text.contains("Назад"))
async def close_settings_menu(message: Message):
    kb = await main_keyboard(message.from_user.id)
    await message.reply("Возвращаюсь назад", reply_markup=kb)


@settings_router.message(F.text.contains("Изменить время окончания дня"))
@settings_router.message(F.text == "/update_finish_day")
async def start_updating_finish_day(message: Message, state: FSMContext):
    await state.set_state(DayFinishForm.day_finish)
    kb = await main_keyboard(message.from_user.id)
    await message.reply(
        "Укажите новое время окончания дня в формате час.минута", reply_markup=kb
    )


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


@settings_router.message(F.text.contains("Изменить дневной лимит"))
@settings_router.message(F.text == "/update_daily_limit")
async def start_updating_daily_limit(message: Message, state: FSMContext):
    await state.set_state(EnergyLimitForm.energy_limit)
    kb = await main_keyboard(message.from_user.id)
    await message.reply("Укажите новый лимит каллорий", reply_markup=kb)


@settings_router.message(EnergyLimitForm.energy_limit)
async def process_energy_limit(message: Message, state: FSMContext):
    await state.clear()
    try:
        limits = get_pfc_limits_from_callories_limit(int(message.text))
        await update_user(
            message.from_user.id,
            {
                "energy_limit": int(message.text),
                "proteins_limit": limits["proteins_limit"],
                "carbohydrates_limit": limits["carbohydrates_limit"],
                "fats_limit": limits["fats_limit"],
            },
        )
        await message.answer(text="Дневной лимит изменён")
    except ValueError:
        await message.answer(text="Неверный формат ввода")
