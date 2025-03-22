# handlers/menu_handler.py

import os
import json
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from services.config_service import get_language

menu_router = Router()

@menu_router.message(Command("menu"))
async def menu_command(message: Message):
    language = get_language(message.from_user.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍣 Sushi", callback_data=f"menu_Sushi_{language}")],
        [InlineKeyboardButton(text="🥢 SETY", callback_data=f"menu_SETY_{language}")],
        [InlineKeyboardButton(text="🔥 Grill", callback_data=f"menu_Grill_{language}")]
    ])
    await message.answer("🔹 Выберите тип меню:", reply_markup=keyboard)

@menu_router.callback_query(lambda c: c.data and c.data.startswith("menu_"))
async def menu_callback(callback: CallbackQuery):
    try:
        _, menu_type, language = callback.data.split("_")
        menu_path = os.path.join("menusc", language, f"{menu_type}.json")
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
        await callback.message.answer("❌ Ошибка загрузки меню.")
    await callback.answer()

def register_menu_handler(dp):
    dp.include_router(menu_router)
