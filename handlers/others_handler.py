# handlers/others_handler.py

from aiogram import Router
from aiogram.types import Message

from services.recommendation_service import ADMIN_KEYWORDS, admin_static_answer, get_combined_menu_keywords
from services.openai_service import ask_openai_companion

others_router = Router()

@others_router.message(
    lambda msg: not msg.text.startswith("/") 
                and not any(kw in msg.text.lower() for kw in get_combined_menu_keywords())
)
async def ai_response(message: Message):
    query_lower = message.text.lower()
    if any(keyword in query_lower for keyword in ADMIN_KEYWORDS):
        answer = admin_static_answer(message.text)
        await message.answer(answer)
    else:
        answer = await ask_openai_companion(message.text, message.from_user.id)
        await message.answer(answer)

def register_others_handler(dp):
    dp.include_router(others_router)
