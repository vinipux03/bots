# test_openai.py

import os
from dotenv import load_dotenv
import openai
import logging

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
logging.basicConfig(level=logging.INFO)

# Минимальный тестовый запрос
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "Ты виртуальная помощница."},
        {"role": "user", "content": "Привет"}
    ]
)
logging.info(f"Test response: {response}")
print("Ответ:", response.choices[0].message.content)
