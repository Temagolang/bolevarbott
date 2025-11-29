"""Репозиторий для работы с подарками в базе данных."""

import logging
from typing import List, Optional
from src.database.connection import get_db_connection
from src.models import Gift

logger = logging.getLogger(__name__)


class GiftRepository:
    """Репозиторий для управления подарками в БД."""

    def __init__(self):
        self.db = get_db_connection()

    async def add_or_update(self, gift: Gift) -> None:
        """Добавляет или обновляет подарок в БД."""
        query = """
            INSERT INTO gifts (name, model, price, floor_price, photo_url, model_rarity, gift_id, user_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (user_id, name, model)
            DO UPDATE SET
                price = EXCLUDED.price,
                floor_price = EXCLUDED.floor_price,
                photo_url = EXCLUDED.photo_url,
                model_rarity = EXCLUDED.model_rarity,
                gift_id = EXCLUDED.gift_id
        """
        try:
            await self.db.pool.execute(
                query,
                gift.name,
                gift.model,
                gift.price,
                gift.floor_price,
                gift.photo_url,
                gift.model_rarity,
                gift.gift_id,
                gift.user_id,
            )
            logger.info(f"Gift '{gift.name}' ({gift.model}) saved for user {gift.user_id}")
        except Exception as e:
            logger.error(f"Failed to save gift: {e}")
            raise

    async def get_all(self) -> List[Gift]:
        """Получает все подарки из БД."""
        query = "SELECT * FROM gifts"
        try:
            rows = await self.db.pool.fetch(query)
            return [Gift.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch all gifts: {e}")
            raise

    async def get_by_user(self, user_id: int) -> List[Gift]:
        """Получает все подарки конкретного пользователя."""
        query = "SELECT * FROM gifts WHERE user_id = $1"
        try:
            rows = await self.db.pool.fetch(query, user_id)
            return [Gift.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch gifts for user {user_id}: {e}")
            raise

    async def update_prices(
        self, user_id: int, name: str, model: str, new_price: float, new_floor: float
    ) -> None:
        """Обновляет цены для конкретного подарка."""
        query = """
            UPDATE gifts
            SET price = $1, floor_price = $2
            WHERE user_id = $3 AND name = $4 AND model = $5
        """
        try:
            await self.db.pool.execute(query, new_price, new_floor, user_id, name, model)
            logger.info(f"Prices updated for '{name}' ({model}) for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to update prices: {e}")
            raise

    async def delete(self, user_id: int, name: str, model: str) -> None:
        """Удаляет подарок из БД."""
        query = "DELETE FROM gifts WHERE user_id = $1 AND name = $2 AND model = $3"
        try:
            await self.db.pool.execute(query, user_id, name, model)
            logger.info(f"Gift '{name}' ({model}) deleted for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete gift: {e}")
            raise
