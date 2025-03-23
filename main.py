# main.py

import os
from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные окружения сразу!

import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импортируем функцию, которая зарегистрирует все хендлеры
from handlers import register_handlers
# Импортируем middleware для логирования
from utils.logging_middleware import LoggingMiddleware
# Импортируем функцию для установки /commands
from services.config_service import set_bot_commands

def main():
    # Отладочный вывод для проверки загрузки OPENAI_API_KEY
    openai_api_key = os.getenv("OPENAI_API_KEY")
    print("OPENAI_API_KEY:", openai_api_key)

    TOKEN = os.getenv("BOT_TOKEN")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    scheduler = AsyncIOScheduler()

    # Регистрируем хендлеры (из папки /handlers)
    register_handlers(dp)

    # Используем собственное middleware для логирования
    dp.message.middleware(LoggingMiddleware())

    async def startup():
        await bot.delete_webhook(drop_pending_updates=True)
        await set_bot_commands(bot)  # Устанавливаем /commands
        scheduler.start()
        await dp.start_polling(bot)

    asyncio.run(startup())

if __name__ == "__main__":
    main()

from routers.smart_router import smart_router
dp.message()(smart_router)
