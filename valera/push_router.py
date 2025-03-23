import os
from git import Repo

# === НАСТРОЙКИ ===
GITHUB_TOKEN = "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"
REPO_URL = f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/vinipux03/bots.git"
LOCAL_PATH = "bots_clone"
COMMIT_MSG = "🧠 Добавлен интеллектуальный маршрутизатор smart_router"

# === КЛОНИРОВАНИЕ ===
if not os.path.exists(LOCAL_PATH):
    Repo.clone_from(REPO_URL, LOCAL_PATH)

repo = Repo(LOCAL_PATH)
router_path = os.path.join(LOCAL_PATH, "routers")
os.makedirs(router_path, exist_ok=True)

# === КОД ИЗ CANVAS ===
router_code = '''from aiogram import types
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
'''

with open(os.path.join(router_path, "smart_router.py"), "w", encoding="utf-8") as f:
    f.write(router_code)

# === ДОБАВЛЯЕМ В main.py ===
main_path = os.path.join(LOCAL_PATH, "main.py")
with open(main_path, "a", encoding="utf-8") as f:
    f.write("\nfrom routers.smart_router import smart_router\ndp.message()(smart_router)\n")

# === COMMIT + PUSH ===
repo.git.add(all=True)
repo.index.commit(COMMIT_MSG)
repo.remote(name="origin").push()
print("✅ УСПЕХ! Код залит в репозиторий.")
