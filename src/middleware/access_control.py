"""Middleware для контроля доступа к боту."""

import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from src.config import get_settings

logger = logging.getLogger(__name__)


class AccessControlMiddleware(BaseMiddleware):
    """Middleware для проверки доступа пользователей к боту."""

    def __init__(self):
        self.settings = get_settings()
        self.allowed_users = self.settings.allowed_users
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Проверяет доступ пользователя перед обработкой события."""

        # Если whitelist не настроен - пропускаем всех
        if not self.allowed_users:
            return await handler(event, data)

        # Получаем username пользователя
        user = event.from_user
        username = user.username

        # Проверяем доступ
        if username and username in self.allowed_users:
            # Разрешённый пользователь - пропускаем
            logger.info(f"Access granted for user @{username} (id: {user.id})")
            return await handler(event, data)
        else:
            # Неразрешённый пользователь - отправляем "средний палец"
            logger.warning(
                f"Access denied for user @{username or 'NO_USERNAME'} "
                f"(id: {user.id}, name: {user.full_name})"
            )

            # Формируем сообщение
            response = (
                "🖕\n\n"
                "Доступ запрещён.\n"
                "Этот бот только для избранных."
            )

            # Отправляем в зависимости от типа события
            if isinstance(event, Message):
                await event.answer(response)
            elif isinstance(event, CallbackQuery):
                await event.answer("🖕 Доступ запрещён", show_alert=True)
                await event.message.answer(response)

            # Прерываем обработку
            return None