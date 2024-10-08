from aiogram.types import Message, LabeledPrice, CallbackQuery, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from db.functions import (
    get_promocode,
    get_user,
    update_user,
    update_promocode_quantity,
    update_user_balance,
)
from config import logger
from keyboards import payment_keyboard, payment_size_keyboard, main_keyboard


class Promocode(StatesGroup):
    password = State()


payment_router = Router()


@payment_router.message(F.text.contains("Ввести промокод"))
async def start_enetering_promocode(message: Message, state: FSMContext):
    await state.set_state(Promocode.password)
    await message.reply("Введите промокод")


@payment_router.message(Promocode.password)
async def entered_promocode(message: Message, state: FSMContext):
    await state.clear()
    password = message.text
    user_id = message.from_user.id
    promocode = await get_promocode(password)
    try:
        if promocode is None:
            await message.answer(text="Неверный промокод")
            return None

        if promocode["remaining_quantity"] <= 0:
            await message.answer(
                text="Промоакция завершена, все промокоды израсходованы"
            )
            return None

        user = await get_user(user_id)
        await update_user(
            user_id,
            {"balance": int(user.get("balance", 0)) + int(promocode["balance_boost"])},
        )
        await message.answer(text="Баланс успешно пополнен")
        if promocode["aux_property"] != "unlimited":
            await update_promocode_quantity(
                password, int(promocode["remaining_quantity"]) - 1
            )
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Что-то пошло не так")


@payment_router.message(F.text.contains("Пополнить счёт"))
async def send_payment_sizes(message: Message):
    await message.reply("Выберите размер платежа", reply_markup=payment_size_keyboard())


@payment_router.callback_query(F.data.startswith("cancel_payment"))
async def cancel_payment(call: CallbackQuery):
    await call.message.answer(text="Отменяю платёж", reply_markup=main_keyboard())


@payment_router.message(F.text.contains("Пополнить на"))
async def send_invoice_handler(message: Message):
    size = int(message.text.split(" ")[-1])
    prices = [
        LabeledPrice(label="XTR", amount=size),
    ]
    await message.answer_invoice(
        title="Пополнить счёт",
        description=f"Пополнить счёт на {size} ⭐️",
        prices=prices,
        provider_token="",
        payload=f"pay_{size}",
        currency="XTR",
        reply_markup=payment_keyboard(size),
    )


@payment_router.pre_checkout_query()
async def on_pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery,
):
    await pre_checkout_query.answer(ok=True)


@payment_router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    user_id = message.from_user.id
    size = int(message.successful_payment.invoice_payload.split("_")[-1])
    user = await get_user(user_id)
    await update_user_balance(user_id, int(user["balance"]) + size)
    await message.answer(
        text="Оплата прошла успешно, средства зачислены на ваш аккаунт",
        message_effect_id="5104841245755180586",
        reply_markup=main_keyboard(),
    )
