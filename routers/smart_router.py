from aiogram import types
from rgbar import get_language, recommend_dish, menu_command
import asyncio

# 🔍 Ключевые слова
ORDER_WORDS = [
    "заказать", "сделать заказ", "оформить", "добавь в корзину",
    "оплата", "хочу заказать"
]

MENU_WORDS = [
    "меню", "что есть", "ассортимент", "выбор", "блюда",
    "что можно заказать", "покажи", "голоден", "ужин", "завтрак", "обед"
]

RECOMMEND_WORDS = [
    "посоветуй", "рекомендуешь", "что вкусное", "предложи", "удиви", "что бы ты выбрала"
]

CATEGORY_WORDS = {
    "sushi": ["суши", "роллы", "маки"],
    "grill": ["гриль", "мясо", "барбекю", "шашлык", "стейк"],
    "sety": ["сеты", "сет", "комбо", "на двоих", "на компанию"]
}

# 🧠 Интеллектуальный роутер
async def smart_router(message: types.Message):
    text = message.text.lower()
    user_id = message.from_user.id
    language = get_language(user_id)

    if any(word in text for word in ORDER_WORDS):
        await message.answer("Чтобы оформить заказ, открой меню через /menu и выбери блюдо. Я помогу с оформлением!")
        return

    if any(word in text for word in MENU_WORDS):
        await menu_command(message)
        return

    for category, words in CATEGORY_WORDS.items():
        if any(word in text for word in words):
            recommendation = await recommend_dish(text, user_id, language)
            await message.answer(recommendation, parse_mode="HTML")
            return

    if any(word in text for word in RECOMMEND_WORDS):
        await message.answer("Секундочку, подберу для тебя что-то вкусненькое... 🍣")
        await asyncio.sleep(2)
        recommendation = await recommend_dish(text, user_id, language)
        await message.answer(recommendation, parse_mode="HTML")
