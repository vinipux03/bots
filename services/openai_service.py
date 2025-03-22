import os
import logging
import json
import openai
import asyncio

from services.config_service import user_data

# Устанавливаем API-ключ (load_dotenv() должен быть вызван в main.py)
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_companion_system_prompt(user_id):
    user = user_data.get(user_id, {})
    # Если пользователь мужчина – используем профиль для виртуального парня, иначе – для виртуальной девушки.
    filename = "bot_men.json" if user.get("gender") == "male" else "bot_woomen.json"
    path = os.path.join("gender_bot", filename)
    logging.info(f"Попытка открыть файл: {path}")
    if not os.path.exists(path):
        logging.error(f"Файл не найден: {path}")
        return "Ты – помощник."  # fallback
    with open(path, "r", encoding="utf-8") as f:
        try:
            companion_data = json.load(f)
            logging.info(f"Содержимое файла {filename}: {companion_data}")
        except Exception as ex:
            logging.error(f"Ошибка при загрузке JSON из {filename}: {ex}")
            return "Ты – помощник."
    role = companion_data.get("bot_profile", {}).get("role", "помощник")
    description = companion_data.get("bot_profile", {}).get("description", "")
    prompt = f"Ты – {role}. {description}"
    logging.info(f"Сформированный системный промпт: {prompt}")
    return prompt

async def ask_openai_companion(prompt, user_id):
    try:
        system_prompt = get_companion_system_prompt(user_id)
        user_message = f"Пользователь спрашивает: {prompt}"
        logging.info(f"User message: {user_message}")
        
        # Используем модель "gpt-3.5-turbo-0125"
        model_name = "gpt-3.5-turbo-0125"
        
        def sync_call():
            return openai.ChatCompletion.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                request_timeout=30,
            )
        response = await asyncio.to_thread(sync_call)
        logging.info(f"OpenAI raw response: {response}")
        
        if not response or not hasattr(response, "choices") or len(response.choices) == 0:
            logging.error("OpenAI вернул пустой ответ")
            return "Произошла ошибка при обработке запроса AI."
        
        content = response.choices[0].message.content.strip()
        logging.info(f"OpenAI ответ: {content}")
        if not content:
            logging.error("Пустой ответ от OpenAI")
            return "Извините, я не смогла получить ответ от сервера."
        
        return content
    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response text: {e.response.text}")
        logging.error(f"OpenAI error (companion): {e}")
        return "Произошла ошибка при обработке запроса AI."
