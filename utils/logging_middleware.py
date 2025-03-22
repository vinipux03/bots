# utils/logging_middleware.py

import logging
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Message

class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        logging.info(f"User {event.from_user.id} ({event.from_user.full_name}) sent: {event.text}")
        return await handler(event, data)
