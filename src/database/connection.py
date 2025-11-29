"""Управление подключением к PostgreSQL базе данных."""

import asyncpg
from typing import Optional
import logging

from src.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Менеджер подключения к PostgreSQL базе данных."""

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Создает пул подключений к базе данных."""
        if self._pool is not None:
            logger.warning("Database pool already exists")
            return

        settings = get_settings()

        try:
            self._pool = await asyncpg.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name,
                min_size=1,
                max_size=10,
            )
            logger.info("Database pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self) -> None:
        """Закрывает пул подключений."""
        if self._pool is None:
            return

        await self._pool.close()
        self._pool = None
        logger.info("Database pool closed")

    @property
    def pool(self) -> asyncpg.Pool:
        """Возвращает пул подключений."""
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized. Call connect() first.")
        return self._pool


# Singleton instance
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Возвращает singleton подключения к БД."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection