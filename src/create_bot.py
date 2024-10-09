from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg import create_pool
from config import PG_DB, PG_PWD, PG_USER, TELEGRAM_TOKEN
import asyncio
from typing import List, Union
from aiogram.dispatcher.middlewares import BaseMiddleware

class AlbumMiddleware(BaseMiddleware):
    album_data: dict = {}
    def __init__(self, latency: Union[int, float] = 0.01):
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            self.album_data[message.from_user.id] = [message]

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.from_user.id]
            await asyncio.sleep(self.latency)
        else:
            try:
                self.album_data[message.media_group_id].append(message)
                return None
            except KeyError:
                self.album_data[message.media_group_id] = [message]
                await asyncio.sleep(self.latency)

                message.conf["is_last"] = True
                data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message):
        if not message.media_group_id:
            if message.from_user.id and message.conf.get("is_last"):
                del self.album_data[message.from_user.id]
        else:
            if message.media_group_id and message.conf.get("is_last"):
                del self.album_data[message.media_group_id]

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
