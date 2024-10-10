from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg import create_pool
from config import PG_DB, PG_PWD, PG_USER, TELEGRAM_TOKEN
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n.middleware import SimpleI18nMiddleware


async def init_db_postgres():
    pool = await create_pool(
        user=PG_USER, password=PG_PWD, host="postgres", database=PG_DB
    )
    return pool


# i18n = I18n(path="locales", default_locale="en", domain="messages")
# i18n_middleware = SimpleI18nMiddleware(i18n)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
bot = Bot(
    token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
