import asyncio
from create_bot import bot, dp, scheduler, init_db_postgres
from handlers import start_router, settings_router, tracker_router, payment_router
from db.functions import finish_day_check_all_users
from db.client import PGClient
from db.init_db_values import init_all_db_values


async def main():
    dp.include_router(start_router)
    dp.include_router(settings_router)
    dp.include_router(tracker_router)
    dp.include_router(payment_router)

    pool = await init_db_postgres()
    dp["pg_client"] = PGClient(pool)

    await init_all_db_values()
    # запуск бота в режиме long polling при запуске бот очищает все обновления, которые были за его моменты бездействия
    try:
        scheduler.add_job(finish_day_check_all_users, "interval", seconds=60)
        scheduler.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
