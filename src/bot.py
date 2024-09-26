import asyncio
from create_bot import bot, dp
from handlers.user_handlers import user_router
from aiogram.types import BotCommand, BotCommandScopeDefault


# Функция, которая настроит командное меню (дефолтное для всех пользователей)
# async def set_commands():
#     commands = [BotCommand(command='start', description='Старт'),
#                 BotCommand(command='profile', description='Мой профиль')]
#     await bot.set_my_commands(commands, BotCommandScopeDefault())


async def main():
    # регистрация роутеров
    dp.include_router(user_router)
    # dp.include_router(admin_router)

    # регистрация функций при старте и завершении работы бота
    # dp.startup.register(start_bot)
    # dp.shutdown.register(stop_bot)

    # запуск бота в режиме long polling при запуске бот очищает все обновления, которые были за его моменты бездействия
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())