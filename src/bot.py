import asyncio
from create_bot import bot, dp, scheduler
from handlers.user_handlers import user_router
from db.functions import finish_day_check_all_users


async def main():
    # регистрация роутеров
    dp.include_router(user_router)
    # dp.include_router(admin_router)

    # регистрация функций при старте и завершении работы бота
    # dp.startup.register(start_bot)
    # dp.shutdown.register(stop_bot)

    # запуск бота в режиме long polling при запуске бот очищает все обновления, которые были за его моменты бездействия
    try:
        scheduler.add_job(finish_day_check_all_users, 'interval', seconds=60)
        scheduler.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())