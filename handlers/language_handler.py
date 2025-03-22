# handlers/language_handler.py

from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram import F

from services.config_service import LANGUAGE_CODES, user_data, user_languages

language_router = Router()

@language_router.message(Command("language"))
async def change_language(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang)] for lang in LANGUAGE_CODES.keys()],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("🌍 Выберите язык общения:", reply_markup=keyboard)

@language_router.message(F.text.in_(LANGUAGE_CODES.keys()))
async def set_language(message: Message):
    user_languages[message.from_user.id] = LANGUAGE_CODES[message.text]
    if message.from_user.id in user_data:
        user_data[message.from_user.id]["language"] = LANGUAGE_CODES[message.text]
    await message.answer(f"✅ Язык изменен на {message.text}", reply_markup=None)

def register_language_handler(dp):
    dp.include_router(language_router)
