"""Кэш для маппинга username -> user_id."""

import logging
from typing import Optional, List
from src.config import get_settings

logger = logging.getLogger(__name__)


class UserCache:
    """Кэш для хранения маппинга username <-> user_id."""

    def __init__(self):
        self._cache: dict[str, int] = {}  # username -> user_id
        self._reverse_cache: dict[int, str] = {}  # user_id -> username

    def add_user(self, username: str, user_id: int) -> None:
        """Добавляет пользователя в кэш."""
        if username:
            self._cache[username] = user_id
            self._reverse_cache[user_id] = username
            logger.debug(f"User cached: {username} <-> {user_id}")

    def get_user_id(self, username: str) -> Optional[int]:
        """Получает user_id по username."""
        return self._cache.get(username)

    def get_username(self, user_id: int) -> Optional[str]:
        """Получает username по user_id."""
        return self._reverse_cache.get(user_id)

    def get_group_user_ids(self, username: str) -> List[int]:
        """
        Получает user_id всех пользователей из группы данного пользователя.

        Args:
            username: Username пользователя

        Returns:
            Список user_id всех пользователей группы
        """
        settings = get_settings()
        group_members = settings.get_group_members(username)

        user_ids = []
        for member in group_members:
            user_id = self.get_user_id(member)
            if user_id:
                user_ids.append(user_id)
            else:
                logger.warning(f"User {member} from group not found in cache")

        # Если не нашли всех членов группы, вернём хотя бы текущего пользователя
        if not user_ids:
            current_user_id = self.get_user_id(username)
            if current_user_id:
                user_ids = [current_user_id]

        return user_ids

    def get_group_user_ids_by_user_id(self, user_id: int) -> List[int]:
        """
        Получает user_id всех пользователей из группы по user_id.

        Args:
            user_id: ID пользователя

        Returns:
            Список user_id всех пользователей группы
        """
        # Получаем username по user_id
        username = self.get_username(user_id)

        if not username:
            # Если username не найден в кэше, возвращаем только текущего пользователя
            logger.warning(f"Username not found for user_id {user_id}, returning only this user")
            return [user_id]

        # Используем существующий метод
        return self.get_group_user_ids(username)


# Глобальный singleton кэша
_user_cache: Optional[UserCache] = None


def get_user_cache() -> UserCache:
    """Возвращает singleton кэша пользователей."""
    global _user_cache
    if _user_cache is None:
        _user_cache = UserCache()
    return _user_cache