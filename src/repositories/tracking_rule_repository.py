"""Репозиторий для работы с правилами отслеживания."""

import logging
from typing import List, Optional
from src.database.connection import get_db_connection
from src.models import TrackingRule

logger = logging.getLogger(__name__)


class TrackingRuleRepository:
    """Репозиторий для управления правилами отслеживания в БД."""

    def __init__(self):
        self.db = get_db_connection()

    async def create(self, rule: TrackingRule) -> int:
        """
        Создает новое правило отслеживания.

        Returns:
            ID созданного правила
        """
        query = """
            INSERT INTO tracking_rules (
                user_id, collection_name, model, condition_type,
                target_price, floor_discount_percent, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """
        try:
            row = await self.db.pool.fetchrow(
                query,
                rule.user_id,
                rule.collection_name,
                rule.model,
                rule.condition_type.value,
                rule.target_price,
                rule.floor_discount_percent,
                rule.is_active,
            )
            rule_id = row["id"]
            logger.info(f"Tracking rule created: ID={rule_id}, user={rule.user_id}")
            return rule_id
        except Exception as e:
            logger.error(f"Failed to create tracking rule: {e}")
            raise

    async def get_by_id(self, rule_id: int) -> Optional[TrackingRule]:
        """Получает правило по ID."""
        query = "SELECT * FROM tracking_rules WHERE id = $1"
        try:
            row = await self.db.pool.fetchrow(query, rule_id)
            if row:
                return TrackingRule.from_db_row(dict(row))
            return None
        except Exception as e:
            logger.error(f"Failed to fetch tracking rule {rule_id}: {e}")
            raise

    async def get_by_user(self, user_id: int, active_only: bool = False) -> List[TrackingRule]:
        """
        Получает все правила пользователя.

        Args:
            user_id: ID пользователя
            active_only: Если True, возвращает только активные правила
        """
        if active_only:
            query = "SELECT * FROM tracking_rules WHERE user_id = $1 AND is_active = TRUE"
        else:
            query = "SELECT * FROM tracking_rules WHERE user_id = $1"

        try:
            rows = await self.db.pool.fetch(query, user_id)
            return [TrackingRule.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch rules for user {user_id}: {e}")
            raise

    async def get_by_user_ids(self, user_ids: List[int], active_only: bool = False) -> List[TrackingRule]:
        """
        Получает правила для списка пользователей (для группы).

        Args:
            user_ids: Список ID пользователей
            active_only: Если True, возвращает только активные правила
        """
        if not user_ids:
            return []

        if active_only:
            query = "SELECT * FROM tracking_rules WHERE user_id = ANY($1) AND is_active = TRUE ORDER BY created_at DESC"
        else:
            query = "SELECT * FROM tracking_rules WHERE user_id = ANY($1) ORDER BY created_at DESC"

        try:
            rows = await self.db.pool.fetch(query, user_ids)
            return [TrackingRule.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch rules for user group: {e}")
            raise

    async def get_all_active(self) -> List[TrackingRule]:
        """Получает все активные правила (для Price Tracker)."""
        query = "SELECT * FROM tracking_rules WHERE is_active = TRUE"
        try:
            rows = await self.db.pool.fetch(query)
            return [TrackingRule.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch active rules: {e}")
            raise

    async def update(self, rule: TrackingRule) -> None:
        """Обновляет существующее правило."""
        query = """
            UPDATE tracking_rules
            SET collection_name = $1,
                model = $2,
                condition_type = $3,
                target_price = $4,
                floor_discount_percent = $5,
                is_active = $6
            WHERE id = $7
        """
        try:
            await self.db.pool.execute(
                query,
                rule.collection_name,
                rule.model,
                rule.condition_type.value,
                rule.target_price,
                rule.floor_discount_percent,
                rule.is_active,
                rule.rule_id,
            )
            logger.info(f"Tracking rule {rule.rule_id} updated")
        except Exception as e:
            logger.error(f"Failed to update tracking rule: {e}")
            raise

    async def toggle_active(self, rule_id: int) -> bool:
        """
        Переключает статус активности правила.

        Returns:
            Новый статус is_active
        """
        query = """
            UPDATE tracking_rules
            SET is_active = NOT is_active
            WHERE id = $1
            RETURNING is_active
        """
        try:
            row = await self.db.pool.fetchrow(query, rule_id)
            new_status = row["is_active"]
            logger.info(f"Rule {rule_id} active status toggled to {new_status}")
            return new_status
        except Exception as e:
            logger.error(f"Failed to toggle rule status: {e}")
            raise

    async def delete(self, rule_id: int) -> None:
        """Удаляет правило."""
        query = "DELETE FROM tracking_rules WHERE id = $1"
        try:
            await self.db.pool.execute(query, rule_id)
            logger.info(f"Tracking rule {rule_id} deleted")
        except Exception as e:
            logger.error(f"Failed to delete rule: {e}")
            raise