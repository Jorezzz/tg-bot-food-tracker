from aiogram.types import Message, LabeledPrice, CallbackQuery, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, F
from config import logger, PAYMENT_TOKEN
from db.users import (
    get_user,
    update_user,
)
from db.promocodes import (
    get_promocode,
    update_promocode_quantity,
)
from db.payments import update_user_balance
from keyboards import payment_keyboard, payment_size_keyboard, main_keyboard
import json


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
            {"balance": user["balance"] + promocode["balance_boost"]},
        )
        await message.answer(text="Баланс успешно пополнен")
        if promocode["aux_property"] != "unlimited":
            await update_promocode_quantity(
                password, promocode["remaining_quantity"] - 1
            )
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Что-то пошло не так")


@payment_router.message(F.text.contains("Пополнить баланс"))
async def send_payment_sizes(message: Message):
    await message.reply(
        "Выберите размер пополнения", reply_markup=payment_size_keyboard()
    )


@payment_router.callback_query(F.data.startswith("cancel_payment"))
async def cancel_payment(call: CallbackQuery):
    await call.message.answer(text="Отменяю платёж", reply_markup=main_keyboard())


@payment_router.callback_query(F.data.startswith("pay_"))
async def send_invoice_handler(call: CallbackQuery):
    balance_payment = int(call.data.split("_")[1])
    user_payment = int(call.data.split("_")[2])
    prices = [
        LabeledPrice(label="RUB", amount=user_payment * 100),
    ]
    await call.message.answer_invoice(
        title="Пополнить баланс",
        description=f"Пополнить баланс на {balance_payment} ⭐️",
        prices=prices,
        provider_token=PAYMENT_TOKEN,
        payload=f"pay_{balance_payment}",
        currency="RUB",
        reply_markup=payment_keyboard(user_payment),
        need_email=True,
        send_email_to_provider=True,
        provider_data=json.dumps(
            {
                "receipt": {
                    "items": [
                        {
                            "description": f"Пополнение счёта на {balance_payment} баллов",
                            "quantity": "1",
                            "amount": {
                                "value": f"{user_payment}.00",
                                "currency": "RUB",
                            },
                            "vat_code": 1,
                        }
                    ]
                }
            }
        ),
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
    await update_user_balance(user_id, user["balance"] + size)
    await message.answer(
        text="Оплата прошла успешно, средства зачислены на ваш аккаунт",
        reply_markup=main_keyboard(),
    )
