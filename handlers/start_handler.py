# handlers/start_handler.py

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

# Импортируем нужные функции из сервисов
from services.config_service import load_config, get_language, user_data, get_user_info

start_router = Router()

@start_router.message(Command("start"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # Определяем гендер (примерная логика)
    gender = "male" if message.from_user.username else "female"

    user_info = get_user_info(user_id, first_name, gender)
    name = user_info["name"]
    polite_form = user_info["polite"]

    config = load_config(user_info["language"])
    goal = config.get("goal", "Добро пожаловать в кафе 'rg-bar'. Я Ника, ваша администраторка...")
    await message.answer(f"Привет, {polite_form} {name}! 🎓 {goal}\n\n")

def register_start_handler(dp):
    dp.include_router(start_router)
