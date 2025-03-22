# services/config_service.py

import os
import json
import logging

from aiogram import Bot, types

DEFAULT_LANGUAGE = "uk"

LANGUAGE_CODES = {
    "Українська 🇺🇦 (Українська)": "uk",
    "Русский 🇷🇺 (Русский)": "ru",
    "Čeština 🇨🇿 (Čeština)": "cs",
    "English 🇬🇧 (English)": "en",
    "Moldovenească 🇲🇩 (Moldovenească)": "md",
    "Română 🇷🇴 (Română)": "ro"
}

user_data = {}
user_languages = {}

def get_user_info(user_id, first_name, gender):
    if user_id not in user_data:
        polite_form = "дорогой" if gender == "male" else "дорогая"
        user_data[user_id] = {
            "name": first_name,
            "gender": gender,
            "polite": polite_form,
            "language": DEFAULT_LANGUAGE
        }
    return user_data[user_id]

def get_language(user_id):
    return user_data.get(user_id, {}).get("language", DEFAULT_LANGUAGE)

def load_config(language=DEFAULT_LANGUAGE):
    config_file = os.path.join("configs", f"config_{language}.json")
    if not os.path.exists(config_file):
        logging.error(f"Файл {config_file} не найден. Загружается конфигурация по умолчанию.")
        language = DEFAULT_LANGUAGE
        config_file = os.path.join("configs", f"config_{language}.json")
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.error(f"Ошибка загрузки конфигурации из {config_file}.")
        return {}

async def set_bot_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="language", description="Выбрать язык"),
        types.BotCommand(command="menu", description="Ассортимент кафе"),
        types.BotCommand(command="contacts", description="Адрес и телефон"),
        types.BotCommand(command="website", description="Сайт кафе"),
        types.BotCommand(command="bots", description="Полезные боты"),
        types.BotCommand(command="support", description="Тех. поддержка")
    ]
    await bot.set_my_commands(commands)
