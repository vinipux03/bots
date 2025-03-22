# handlers/__init__.py

from aiogram import Dispatcher

# Импортируем все хендлеры
from .start_handler import register_start_handler
from .menu_handler import register_menu_handler
from .language_handler import register_language_handler
from .common_handler import register_common_handlers
from .others_handler import register_others_handler

def register_handlers(dp: Dispatcher):
    # По очереди «подключаем» все группы хендлеров
    register_start_handler(dp)
    register_menu_handler(dp)
    register_language_handler(dp)
    register_common_handlers(dp)
    register_others_handler(dp)
