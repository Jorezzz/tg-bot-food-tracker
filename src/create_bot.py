from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg import create_pool
from config import PG_DB, PG_PWD, PG_USER, TELEGRAM_TOKEN


async def init_db_postgres():
    pool = await create_pool(
        user=PG_USER, password=PG_PWD, host="postgres", database=PG_DB
    )
    return pool


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
bot = Bot(
    token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
