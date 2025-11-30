"""Конфигурация приложения из переменных окружения."""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class Settings:
    """Настройки приложения."""

    # Telegram Bot
    bot_token: str
    api_id: int
    api_hash: str

    # Database (PostgreSQL)
    db_host: str
    db_user: str
    db_password: str
    db_name: str
    db_port: int = 5432

    # Price Tracker
    price_check_interval: int = 60  # seconds
    use_mock_api: bool = True  # Use mock API instead of real Portals API

    # Access Control
    allowed_users: list[str] = None  # Список разрешённых username
    user_groups: dict[str, str] = None  # Группы пользователей {username: group_id}

    @classmethod
    def from_env(cls) -> "Settings":
        """Загружает настройки из переменных окружения."""
        # Попытка загрузить .env файл если он существует
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)

        # Парсим список разрешённых пользователей
        allowed_users_str = os.getenv("ALLOWED_USERS", "")
        allowed_users = [u.strip() for u in allowed_users_str.split(",") if u.strip()] if allowed_users_str else []

        # Создаём группы пользователей с user_id
        # user_id для maggmogg = 256986671 (из БД)
        # user_id для FCK_HOTLINE нужно узнать когда он напишет боту
        user_groups = {
            "FCK_HOTLINE": {"group_id": "team1", "user_ids": [256986671]},  # Пока только maggmogg
            "maggmogg": {"group_id": "team1", "user_ids": [256986671]},
        }

        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            api_id=int(os.getenv("API_ID", "0")),
            api_hash=os.getenv("API_HASH", ""),
            db_host=os.getenv("DB_HOST", "localhost"),
            db_user=os.getenv("DB_USER", "postgres"),
            db_password=os.getenv("DB_PASSWORD", ""),
            db_name=os.getenv("DB_NAME", "portals_bot"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            price_check_interval=int(os.getenv("PRICE_CHECK_INTERVAL", "60")),
            use_mock_api=os.getenv("USE_MOCK_API", "true").lower() == "true",
            allowed_users=allowed_users if allowed_users else None,
            user_groups=user_groups,
        )

    def get_user_group(self, username: str) -> Optional[str]:
        """Возвращает ID группы пользователя или None."""
        if not self.user_groups or username not in self.user_groups:
            return None
        return self.user_groups[username].get("group_id")

    def get_group_members(self, username: str) -> list[str]:
        """Возвращает всех пользователей из группы данного пользователя."""
        group_id = self.get_user_group(username)
        if not group_id or not self.user_groups:
            return [username]  # Если нет группы, возвращаем только себя

        # Находим всех пользователей с таким же group_id
        return [user for user, info in self.user_groups.items() if info.get("group_id") == group_id]

    def get_group_user_ids(self, username: str) -> list[int]:
        """Возвращает список user_id всех членов группы."""
        if not self.user_groups or username not in self.user_groups:
            return []

        user_info = self.user_groups[username]
        return user_info.get("user_ids", [])


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Возвращает singleton настроек."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings