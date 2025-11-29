"""Инициализация и настройка Telegram бота."""

import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import get_settings
from src.handlers import register_add_gift_handlers, register_menu_handlers, register_add_tracking_handlers
from src.middleware import AccessControlMiddleware

logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    """Создает экземпляр бота."""
    settings = get_settings()
    return Bot(token=settings.bot_token)


def create_dispatcher() -> Dispatcher:
    """Создает и настраивает диспетчер."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Подключаем middleware для контроля доступа
    dp.message.middleware(AccessControlMiddleware())
    dp.callback_query.middleware(AccessControlMiddleware())
    logger.info("Access control middleware enabled")

    # Регистрируем handlers (порядок важен!)
    register_menu_handlers(dp)  # Меню и навигация
    register_add_tracking_handlers(dp)  # Мастер добавления правил
    register_add_gift_handlers(dp)  # Старый функционал /add (legacy)

    logger.info("Dispatcher created and handlers registered")
    return dp