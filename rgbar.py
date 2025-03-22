import os
import asyncio
import logging
import openai
import json
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования: вывод в консоль (например, в PowerShell)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация клиента OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# --- Middleware для логирования входящих сообщений ---
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        logging.info(f"User {event.from_user.id} ({event.from_user.full_name}) sent: {event.text}")
        return await handler(event, data)

# Регистрируем middleware
dp.message.middleware(LoggingMiddleware())

# Папка с меню и язык по умолчанию
MENU_DIR = "menusc"
DEFAULT_LANGUAGE = "uk"

LANGUAGE_CODES = {
    "Українська 🇺🇦 (Українська)": "uk",
    "Русский 🇷🇺 (Русский)": "ru",
    "Čeština 🇨🇿 (Čeština)": "cs",
    "English 🇬🇧 (English)": "en",
    "Moldovenească 🇲🇩 (Moldovenească)": "md",
    "Română 🇷🇴 (Română)": "ro"
}

# Загрузка стоп-слов и синонимов из файла stopwords.json
def load_stopwords():
    path = os.path.join(MENU_DIR, "stopwords.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Ошибка загрузки стоп-слов из {path}: {e}")
    return {}

STOPWORDS_DATA = load_stopwords()

def get_stop_words(language):
    return STOPWORDS_DATA.get(language, {}).get("stop_words", [])

def get_synonyms(language):
    default_category_keywords = {
        "sushi": ["суши", "рол", "maki", "макі"],
        "grill": ["гриль", "барбекю", "мясо", "шашлык", "стейк"],
        "sety": ["сеты", "сет", "sety", "set"]
    }
    synonyms = STOPWORDS_DATA.get(language, {}).get("synonyms", {})
    return synonyms if synonyms else default_category_keywords

# Дополнительные ключевые фразы для запросов, связанных с меню (заказ на вечер и т.д.)
EXTRA_MENU_PHRASES = {
    "ru": ["на вечер", "на ужин", "вечернее меню", "вечерние блюда", "рекомендуй на вечер", "заказ на вечер"],
    "uk": ["на вечір", "вечірнє меню", "вечірні страви", "рекомендуй на вечір", "замов на вечір"],
    "en": ["evening", "dinner", "evening menu", "suggest dinner", "what to order for dinner"]
}

def get_combined_menu_keywords():
    combined = []
    for d in STOPWORDS_DATA.values():
        combined.extend(d.get("stop_words", []))
    for phrases in EXTRA_MENU_PHRASES.values():
        combined.extend(phrases)
    return combined

# Детекция языка запроса по стоп-словам (из стандартного списка и дополнительных фраз)
def detect_query_language(query: str) -> str:
    query_lower = query.lower()
    for lang, phrases in EXTRA_MENU_PHRASES.items():
        if any(phrase in query_lower for phrase in phrases):
            return lang
    for lang, data in STOPWORDS_DATA.items():
        stop_words = data.get("stop_words", [])
        if any(sw in query_lower for sw in stop_words):
            return lang
    return None

# Словари для хранения данных пользователей и выбранных языков
user_data = {}
user_languages = {}

def get_user_info(user_id, first_name, gender):
    if user_id not in user_data:
        polite_form = "дорогой" if gender == "male" else "дорогая"
        user_data[user_id] = {
            "name": first_name,
            "gender": polite_form,
            "language": DEFAULT_LANGUAGE
        }
    return user_data[user_id]

# Функция загрузки конфигурации для выбранного языка
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

# Функция для загрузки блюд из локальных JSON-файлов меню по выбранному языку и (опционально) категории
def load_dishes(language, specific_category=None):
    dishes = []
    menu_path = os.path.join(MENU_DIR, language)
    file_mapping = {
        "sushi": "Sushi.json",
        "grill": "Grill.json",
        "sety": "SETY.json"
    }
    if specific_category and specific_category.lower() in file_mapping:
        file_path = os.path.join(menu_path, file_mapping[specific_category.lower()])
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for category in data.get("categories", []):
                        dishes.extend(category.get("items", []))
            except Exception as e:
                logging.error(f"Ошибка загрузки блюд из {file_path}: {e}")
    else:
        if os.path.exists(menu_path):
            for filename in os.listdir(menu_path):
                if filename.endswith(".json") and filename.lower() != "stopwords.json":
                    file_path = os.path.join(menu_path, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            for category in data.get("categories", []):
                                dishes.extend(category.get("items", []))
                    except Exception as e:
                        logging.error(f"Ошибка загрузки блюд из {file_path}: {e}")
    return dishes

# Словарь с персональными комментариями для рекомендаций
personal_comments = {
    "sushi": ["Отличный выбор для любителей свежести!", "Эти суши вас не разочаруют!"],
    "grill": ["Для настоящих гурманов!", "Отлично подходит для вечеринки!"],
    "sety": ["Идеальное сочетание вкусов!", "Попробуйте, это хит нашего меню!"],
    "general": ["Приятного аппетита!", "Наслаждайтесь вашим заказом!"]
}

# Функция для обработки запросов к OpenAI (для вопросов, не связанных с меню)
async def ask_openai(prompt, user_id, user_level="A1"):
    try:
        lower_prompt = prompt.lower()
        language = get_language(user_id)
        all_menu_keywords = get_combined_menu_keywords()
        if any(kw in lower_prompt for kw in all_menu_keywords):
            return "Пожалуйста, воспользуйтесь командой /menu для получения рекомендаций из нашего меню."
        
        config = load_config(language)
        system_prompt = config.get("description", "Ты – Ника, администраторка кафе 'rg-bar'. Отвечай на вопросы клиентов.")
        response_style = config.get("response_style", {})
        tone = response_style.get("tone", "Дружелюбный, но профессиональный")
        approach = response_style.get("approach", "Используй понятный язык и вежливость")
        
        user_message = (
            f"Я посетитель кафе 'rg-bar'. "
            f"Пожалуйста, отвечай на {language} языке. "
            f"Стиль: {tone}. Подход: {approach}. "
            f"Мой запрос: {prompt}"
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return "Произошла ошибка при обработке запроса AI."

# Словарь для хранения рекомендаций, чтобы не повторять одни и те же блюда
user_recommendations = {}

# Функция рекомендации блюда из локальных файлов меню с использованием заданного языка
async def recommend_dish(query: str, user_id: int, language: str) -> str:
    query_lower = query.lower()
    synonyms = get_synonyms(language)
    
    target_category = None
    for cat, syn_list in synonyms.items():
        if any(kw in query_lower for kw in syn_list):
            target_category = cat
            break

    rec_category = target_category if target_category else "general"

    if user_id not in user_recommendations:
        user_recommendations[user_id] = {"sushi": set(), "grill": set(), "sety": set(), "general": set()}

    dishes = load_dishes(language, specific_category=target_category) if target_category else load_dishes(language)
    available = [d for d in dishes if d.get("name") not in user_recommendations[user_id][rec_category]]
    if not available:
        user_recommendations[user_id][rec_category] = set()
        available = dishes

    if not available:
        return f"❌ К сожалению, в данный момент нет рекомендаций по {target_category}."

    dish = random.choice(available)
    user_recommendations[user_id][rec_category].add(dish.get("name"))
    comment_list = personal_comments.get(target_category, personal_comments["general"])
    comment = random.choice(comment_list)
    user_info = user_data.get(user_id, {})
    name = user_info.get("name", "друг")
    polite_form = user_info.get("gender", "")
    return (f"{polite_form.capitalize()} {name}, вот моя рекомендация:\n"
            f"<b>{dish.get('name', 'Без названия')}</b> ({dish.get('category', '').capitalize()}) - {dish.get('price', '')}\n"
            f"{dish.get('description', '')}\n\n"
            f"{comment}")

def get_language(user_id):
    return user_data.get(user_id, {}).get("language", DEFAULT_LANGUAGE)

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    gender = "male" if message.from_user.username else "female"
    user_info = get_user_info(user_id, first_name, gender)
    name = user_info["name"]
    polite_form = user_info["gender"]

    config = load_config(user_info["language"])
    goal = config.get("goal", "Добро пожаловать в кафе 'rg-bar'. Я Ника, ваша администраторка. Больше информации: https://www.rg-barliberec.com/")
    await message.answer(f"Привет, {polite_form} {name}! 🎓 {goal}\n\n")

# Обработчик запросов, связанных с меню, на основе комбинированного списка ключевых фраз
@dp.message(lambda message: any(kw in message.text.lower() for kw in get_combined_menu_keywords()))
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

# Обработчик смены языка
@dp.message(Command("language"))
async def change_language(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang)] for lang in LANGUAGE_CODES.keys()],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("🌍 Выберите язык общения:", reply_markup=keyboard)

@dp.message(F.text.in_(LANGUAGE_CODES.keys()))
async def set_language(message: Message):
    user_languages[message.from_user.id] = LANGUAGE_CODES[message.text]
    if message.from_user.id in user_data:
        user_data[message.from_user.id]["language"] = LANGUAGE_CODES[message.text]
    await message.answer(f"✅ Язык изменен на {message.text}", reply_markup=types.ReplyKeyboardRemove())

# Команда для показа меню
@dp.message(Command("menu"))
async def menu_command(message: Message):
    language = get_language(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍣 Sushi", callback_data=f"menu_Sushi_{language}")],
        [InlineKeyboardButton(text="🥢 SETY", callback_data=f"menu_SETY_{language}")],
        [InlineKeyboardButton(text="🔥 Grill", callback_data=f"menu_Grill_{language}")]
    ])
    await message.answer("🔹 Выберите тип меню:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data and c.data.startswith("menu_"))
async def menu_callback(callback: types.CallbackQuery):
    try:
        _, menu_type, language = callback.data.split("_")
        menu_path = os.path.join(MENU_DIR, language, f"{menu_type}.json")
        if not os.path.exists(menu_path):
            await callback.message.edit_text(f"❌ Меню \"{menu_type}\" недоступно для выбранного языка.")
            return
        with open(menu_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        title = data.get("menu_title", menu_type)
        description = data.get("description", "")
        menu_text = f"<b>{title}</b>\n{description}\n\n"
        for category in data.get("categories", []):
            cat_name = category.get("name", "")
            menu_text += f"<u>{cat_name}</u>\n"
            for item in category.get("items", []):
                name = item.get("name", "")
                price = item.get("price", "")
                item_desc = item.get("description", "")
                menu_text += f"🔹 <b>{name}</b> - {price}\n"
                if item_desc:
                    menu_text += f"  {item_desc}\n"
            menu_text += "\n"
        await callback.message.edit_text(menu_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка обработки callback: {e}")
        await callback.message.answer("❌ Ошибка загрузки меню.")
    await callback.answer()

# Общий обработчик сообщений для диалога (если сообщение не содержит ключевых фраз для меню)
@dp.message(lambda message: not message.text.startswith("/") and not any(kw in message.text.lower() for kw in get_combined_menu_keywords()))
async def ai_response(message: Message):
    language = get_language(message.from_user.id)
    response = await ask_openai(message.text, message.from_user.id)
    await message.answer(response)

@dp.message(Command("support"))
async def support_handler(message: Message):
    support_text = "Техническая поддержка: [Mykolacherstvyi](https://t.me/Mykolacherstvyi)"
    await message.answer(support_text, parse_mode="Markdown")

@dp.message(Command("bots"))
async def bots_handler(message: Message):
    bots_text = (
        "Полезные боты:\n"
        "• [@MigrantHelperCZ_bot - юрист](https://t.me/MigrantHelperCZ_bot)\n"
        "• [@Holidayscz_bot - гид по Чехии](https://t.me/Holidayscz_bot)\n"
        "• [@ExamCZBot - учим чешский](https://t.me/ExamCZBot)"
    )
    await message.answer(bots_text, parse_mode="Markdown")

# Новые команды для контактов и официального сайта
@dp.message(Command("contacts"))
async def contacts_handler(message: Message):
    contacts_text = "RG BAR - Tanvaldská 299/299, 463 11 Liberec 30-Vratislavice nad Nisou\n+420 739 462 002"
    await message.answer(contacts_text)

@dp.message(Command("website"))
async def website_handler(message: Message):
    website_text = "https://www.rg-barliberec.com"
    await message.answer(website_text)

# Новая версия функции установки нативных команд
async def set_bot_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="language", description="Выбрать язык"),
        types.BotCommand(command="menu", description="ассортимент кафе"),
        types.BotCommand(command="contacts", description="RG BAR - Tanvaldská 299/299, 463 11 Liberec 30-Vratislavice nad Nisou +420 739 462 002"),
        types.BotCommand(command="website", description="https://www.rg-barliberec.com"),
        types.BotCommand(command="bots", description="Полезные боты"),
        types.BotCommand(command="support", description="Тех. поддержка")
    ]
    await bot.set_my_commands(commands)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
