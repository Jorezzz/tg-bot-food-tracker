import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import redis.asyncio as redis

import os
from dotenv import load_dotenv
from asyncpg import create_pool

# from db.client import PGClient

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OPENAI_TOKEN = os.environ['OPENAI_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
PG_USER = os.environ['PG_USER']
PG_DB = os.environ['PG_DB']
PG_PWD = os.environ['PG_PWD']


async def init_db_postgres():
    pool = await create_pool(
            user=PG_USER, 
            password=PG_PWD, 
            host='postgres', 
            database=PG_DB
    )
    return pool


client = redis.Redis.from_pool(redis.ConnectionPool.from_url("redis://redis:6379/0"))
client_times = redis.Redis.from_pool(redis.ConnectionPool.from_url("redis://redis_timers:6379/0"))

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
bot = Bot(
    token=TELEGRAM_TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)