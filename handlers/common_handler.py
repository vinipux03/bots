# handlers/common_handler.py

import random
import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from services.config_service import get_language, user_data
from services.recommendation_service import recommend_dish, detect_query_language, get_combined_menu_keywords

common_router = Router()

@common_router.message(lambda msg: any(kw in msg.text.lower() for kw in get_combined_menu_keywords()))
async def recommendation_handler(message: Message):
    user_id = message.from_user.id
    detected_lang = detect_query_language(message.text)
    if detected_lang is None:
        detected_lang = get_language(user_id)
    user_info = user_data.get(user_id, {})
    name = user_info.get("name", "друг")
    await message.answer(f"Сейчас посмотрю, {name}...", parse_mode="HTML")
    await asyncio.sleep(random.randint(2, 5))
    recommendation = await recommend_dish(message.text, user_id, detected_lang)
    await message.answer(recommendation, parse_mode="HTML")

@common_router.message(Command("support"))
async def support_handler(message: Message):
    await message.answer("Техническая поддержка: [Mykolacherstvyi](https://t.me/Mykolacherstvyi)", parse_mode="Markdown")

@common_router.message(Command("bots"))
async def bots_handler(message: Message):
    text = (
        "Полезные боты:\n"
        "• [@MigrantHelperCZ_bot - юрист](https://t.me/MigrantHelperCZ_bot)\n"
        "• [@Holidayscz_bot - гид по Чехии](https://t.me/Holidayscz_bot)\n"
        "• [@ExamCZBot - учим чешский](https://t.me/ExamCZBot)"
    )
    await message.answer(text, parse_mode="Markdown")

@common_router.message(Command("contacts"))
async def contacts_handler(message: Message):
    contacts_text = (
        "RG BAR - Tanvaldská 299/299, 463 11 Liberec 30-Vratislavice nad Nisou\n"
        "+420 739 462 002"
    )
    await message.answer(contacts_text)

@common_router.message(Command("website"))
async def website_handler(message: Message):
    await message.answer("https://www.rg-barliberec.com")

def register_common_handlers(dp):
    dp.include_router(common_router)
