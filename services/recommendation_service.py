# services/recommendation_service.py

import os
import json
import logging
import random

MENU_DIR = "menusc"

# Загружаем stopwords
STOPWORDS_DATA = {}
try:
    path = os.path.join(MENU_DIR, "stopwords.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            STOPWORDS_DATA = json.load(f)
except Exception as e:
    logging.error(f"Ошибка загрузки стоп-слов: {e}")

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

personal_comments = {
    "sushi": ["Отличный выбор для любителей свежести!", "Эти суши вас не разочаруют!"],
    "grill": ["Для настоящих гурманов!", "Отлично подходит для вечеринки!"],
    "sety": ["Идеальное сочетание вкусов!", "Попробуйте, это хит нашего меню!"],
    "general": ["Приятного аппетита!", "Наслаждайтесь вашим заказом!"]
}

# Храним рекомендации, чтобы не повторять
user_recommendations = {}

async def recommend_dish(query: str, user_id: int, language: str) -> str:
    from services.config_service import user_data  # чтобы избежать циклического импорта
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
    polite_form = user_info.get("polite", "")

    return (
        f"{polite_form.capitalize()} {name}, вот моя рекомендация:\n"
        f"<b>{dish.get('name', 'Без названия')}</b> ({dish.get('category', '').capitalize()}) - {dish.get('price', '')}\n"
        f"{dish.get('description', '')}\n\n"
        f"{comment}"
    )

# Ключевые слова для запросов к администратору
ADMIN_KEYWORDS = [
    "кафе", "бар", "открыт", "расписание", "бронирование",
    "столик", "контакт", "телефон", "адрес", "администратор"
]

def admin_static_answer(query: str) -> str:
    query_lower = query.lower()
    if "открыт" in query_lower or "расписание" in query_lower:
        return "Наше кафе работает с 10:00 до 22:00."
    elif "бронирование" in query_lower or "столик" in query_lower:
        return "Для бронирования столика, пожалуйста, звоните по телефону +420 739 462 002."
    elif "контакт" in query_lower or "телефон" in query_lower or "адрес" in query_lower:
        return (
            "Адрес кафе: Tanvaldská 299/299, 463 11 Liberec 30-Vratislavice nad Nisou.\n"
            "Телефон: +420 739 462 002."
        )
    else:
        return "Я Ника, администратор кафе 'rg-bar'. Чем могу помочь?"
