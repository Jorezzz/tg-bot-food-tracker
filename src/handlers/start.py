from aiogram import Router, F
from aiogram.types import Message
from config import logger, ADMIN_PASSWORD
from db.users import register_user, get_user, update_user
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import main_keyboard
import hashlib
from aiogram.filters import CommandStart, CommandObject


class AdminPassword(StatesGroup):
    password = State()


start_router = Router()


@start_router.message(CommandStart(deep_link=True))
async def start_deeplink(message: Message, command: CommandObject):
    user = await get_user(message.from_user.id)
    logger.info(f"{command.args}")
    if user is None:
        await register_user(message, balance=20, external_user_id=str(command.args))
    text = """
Привет! Добро пожаловать в @EasyCalloriesBot! 🤖 
Хочешь легко следить за своим питанием? 💪 Я помогу тебе!

📸 Просто сфотографируй свою еду или опиши её текстом, и я мгновенно посчитаю калории! 

❗Чтобы я рассказал тебе о составе блюда, на балансе бота должны быть Telegram Stars. Раз уж ты зашел, я дарю тебе 20 ⭐️! Кстати, 2 ⭐ = 1 распознавание. Начни изучать свой рацион уже сегодня! 😉 

💬 Есть вопросы? Нажми "Помощь" и узнай все о @EasyCalloriesBot
        """
    await message.answer(text=text, reply_markup=main_keyboard())


@start_router.message(F.text == "/start")
async def start(message: Message):
    user = await get_user(message.from_user.id)
    if user is None:
        await register_user(message, balance=20)
    text = """
Привет! Добро пожаловать в @EasyCalloriesBot! 🤖 
Хочешь легко следить за своим питанием? 💪 Я помогу тебе!

📸 Просто сфотографируй свою еду или опиши её текстом, и я мгновенно посчитаю калории! 

❗Чтобы я рассказал тебе о составе блюда, на балансе бота должны быть Telegram Stars. Раз уж ты зашел, я дарю тебе 20 ⭐️! Кстати, 2 ⭐ = 1 распознавание. Начни изучать свой рацион уже сегодня! 😉 

💬 Есть вопросы? Нажми "Помощь" и узнай все о @EasyCalloriesBot
        """
    await message.answer(text=text, reply_markup=main_keyboard())


@start_router.message(F.text == "/register")
async def init_user(message: Message):
    try:
        await register_user(message)
        await message.answer(
            text="Successfully registered", reply_markup=main_keyboard()
        )
    except Exception as e:
        logger.error(f"{e}")
        await message.answer(text="Что-то пошло не так")


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
            await update_user(message.from_user.id, {"role_id": 3})
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
Хочешь легко контролировать свой рацион и следить за калориями? Тогда тебе точно к нам! 😉
 
Вот, как легко начать:
 
📸 Фото-анализ:
 
1️⃣ Сделай фото своего блюда (или выбери из галереи) 📸 или опиши его текстом 
2️⃣ Отправь прямо в чат боту. 
3️⃣ Вуаля! EasyCaloriesBot мгновенно определит калорийность и состав твоей еды.
 
📌 Дополнительные команды:
 
Статус: Проверь свою дневную статистику (калории, БЖУ), баланс и получай персональные рекомендации по питанию. 💪
 
Настройки: Изменяй параметры своего профиля и настраивай бота под себя. ⚙️
 
Пополнить счет: Заряжай свой аккаунт, чтобы продолжать пользоваться всеми возможностями бота. ⭐️
 
Ввести промокод: Не упусти возможность получить скидку! 🎁
 
💬 Часто задаваемые вопросы:
 
Q: Как EasyCaloriesBot помогает? 
A: Он анализирует фото твоего блюда и выдает информацию о калорийности, питательных веществах и ингредиентах.
 
Q: Как сделать идеальное фото для анализа? 
A: Сделай четкое фото с хорошим освещением, на котором видно всё блюдо целиком. 💡 Помни, бот может видеть только то, что представлено на фото, поэтому будь внимателен с необычными ингредиентами.
 
Q: Можно ли удалить блюдо из результатов анализа? 
A: Конечно! После распознавания блюда, ты можешь удалить его или изменить вес порции.
 
 🔥 Присоединяйся к EasyCaloriesBot и сделай свой путь к здоровому питанию легким и приятным!
"""
    await message.answer(text=text, reply_markup=main_keyboard())
