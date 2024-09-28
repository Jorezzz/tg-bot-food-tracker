import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import redis.asyncio as redis
from asyncpg import create_pool
from config import PG_DB, PG_PWD, PG_USER, TELEGRAM_TOKEN

# from db.client import PGClient


async def init_db_postgres():
    pool = await create_pool(
        user=PG_USER, password=PG_PWD, host="postgres", database=PG_DB
    )
    return pool


client = redis.Redis.from_pool(redis.ConnectionPool.from_url("redis://redis:6379/0"))
client_times = redis.Redis.from_pool(
    redis.ConnectionPool.from_url("redis://redis_timers:6379/0")
)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
bot = Bot(
    token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
