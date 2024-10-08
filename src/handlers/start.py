from aiogram import Router, F
from aiogram.types import Message
from config import logger, ADMIN_PASSWORD
from db.functions import register_user, get_user
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import main_keyboard
import hashlib


class AdminPassword(StatesGroup):
    password = State()


start_router = Router()


@start_router.message(F.text == "/start")
async def start(message: Message):
    try:
        await register_user(message)
        # user = await get_user(message.from_user.id)
        # if user is None:
        #     await register_user(message)
        text = """
    🍽️ Приветствуем вас в @EasyCalloriesBot! 🍴

    Мы рады помочь вам следить за вашим рационом!

    📸 Просто отправьте нам фото вашего блюда, и мы определим количество калорий.

    📋 Как это работает:
    1. Сделайте фото вашего блюда или всего приёма пищи или выберите готовое из галереи.
    2. Искуственный интелект предоставит точный расчет калорийности и важных питательных веществ!

    Дополнительные функции:
    1. Трекинг рациона в течения дня.
    2. Персональные рекомендации в течение дня.
    3. Персональная аналитика по итогам дня и рекомендации на будущее.
    4. Возможность изменить время окончания дня (например если вы любите засиживаться до поздна) и дневную норму калорий.

    ❓ У вас вопросы?
    Нажмите кнопку "Помощь" для получения информации о боте и его возможностях.
            """
        await message.answer(text=text, reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Some error ocured")


# @start_router.message(F.text.contains("Регистрация"))
@start_router.message(F.text == "/register")
async def init_user(message: Message):
    try:
        await register_user(message)
        await message.answer(
            text="Successfully registered", reply_markup=main_keyboard()
        )
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
            await message.delete()
            await message.answer(text="Добро пожаловать, повелитель")
        else:
            raise Exception("Wrong admin password")
    except Exception as e:
        logger.error(f"{e}")
        await message.delete()
        await message.answer(text="Неверный пароль, уходи")


@start_router.message(F.text.contains("Помощь"))
@start_router.message(F.text == "/help")
async def help_message(message: Message):
    text = """
**📋 Помощь @EasyCalloriesBot 📋**

---

Добро пожаловать в @EasyCalloriesBot! Мы готовы помочь вам следить за вашим пищевым рационом. Вот список доступных команд и способов использования нашего бота:

### 📸 Как отправить фото:

Чтобы бот мог определить калорийность вашего блюда, выполните следующие шаги:
1. Сделайте фото вашего блюда или выберите готовое из галереи. Помните, что 1 фото стоит 2 балла. 
2. Отправьте фото в этот чат.

### 📌 Остальные команды доступны в меню

1. Статус - Получить статистику по калориям и БЖУ за день, текущий баланс вашего счёта, а также персональную рекомендацию по питанию на день.
2. Настройки - Меню с настройками вашего аккаунта
3. Пополнить счёт - Пополнить счёт вашего аккаунта
4. Ввести промокод - Если у вас есть промокод вы можете есть ввести нажав на эту команду

### ❓ Часто задаваемые вопросы:

**В: Чем может помочь @EasyCalloriesBot?**
**О: Бот анализирует фото вашего блюда и предоставляет информацию о калорийности, основных питательных веществах и отдельных ингредиентах.**

**В: Как сделать фото, чтобы анализ был максимально точным?**
**О: Убедитесь, что фото четкое, в хорошем освещении и на нем видно всё блюдо целиком, в идеале немного под углом, чтобы можно было визуально оценить размер порций. Избегайте размытия и помех на изображении. Однако помните - Бот может видеть только то что представленно на фото и может не знать информацию о приготовлении блюда или о необычных ингридиентах в его составе.**

**В: Могу ли я удалить блюдо из результата распознавания?**
**О: Конечно! Под сообщением бота будут выведены названия распознанных блюд. Нажав на него вам будет предоложен вариант удалить блюдо (если допустим вы передумали его кушать) либо изменить вес, на случай если вы скушали не всё.**
"""
    await message.answer(text=text, reply_markup=main_keyboard())
