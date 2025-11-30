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

        # Создаём группы пользователей (пока хардкод для FCK_HOTLINE и maggmogg)
        # В будущем можно вынести в .env как USER_GROUPS=group1:user1,user2;group2:user3
        user_groups = {
            "FCK_HOTLINE": "team1",
            "maggmogg": "team1",
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
        if not self.user_groups:
            return None
        return self.user_groups.get(username)

    def get_group_members(self, username: str) -> list[str]:
        """Возвращает всех пользователей из группы данного пользователя."""
        group_id = self.get_user_group(username)
        if not group_id or not self.user_groups:
            return [username]  # Если нет группы, возвращаем только себя

        # Находим всех пользователей с таким же group_id
        return [user for user, gid in self.user_groups.items() if gid == group_id]


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Возвращает singleton настроек."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings