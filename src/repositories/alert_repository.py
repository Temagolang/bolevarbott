"""Репозиторий для работы с алертами (уведомлениями)."""

import logging
from typing import List, Optional
from datetime import datetime
from src.database.connection import get_db_connection
from src.models import Alert

logger = logging.getLogger(__name__)


class AlertRepository:
    """Репозиторий для управления алертами в БД."""

    def __init__(self):
        self.db = get_db_connection()

    async def create(self, alert: Alert) -> int:
        """
        Создает новый алерт.

        Returns:
            ID созданного алерта
        """
        query = """
            INSERT INTO alerts (
                rule_id, user_id, lot_id, lot_price, lot_floor_price,
                collection_name, model, photo_url, lot_url
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """
        try:
            row = await self.db.pool.fetchrow(
                query,
                alert.rule_id,
                alert.user_id,
                alert.lot_id,
                alert.lot_price,
                alert.lot_floor_price,
                alert.collection_name,
                alert.model,
                alert.photo_url,
                alert.lot_url,
            )
            alert_id = row["id"]
            logger.info(f"Alert created: ID={alert_id}, rule={alert.rule_id}, lot={alert.lot_id}")
            return alert_id
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise

    async def get_by_id(self, alert_id: int) -> Optional[Alert]:
        """Получает алерт по ID."""
        query = "SELECT * FROM alerts WHERE id = $1"
        try:
            row = await self.db.pool.fetchrow(query, alert_id)
            if row:
                return Alert.from_db_row(dict(row))
            return None
        except Exception as e:
            logger.error(f"Failed to fetch alert {alert_id}: {e}")
            raise

    async def get_by_rule(self, rule_id: int, limit: int = 10) -> List[Alert]:
        """
        Получает последние алерты по правилу.

        Args:
            rule_id: ID правила
            limit: Максимальное количество результатов
        """
        query = """
            SELECT * FROM alerts
            WHERE rule_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        try:
            rows = await self.db.pool.fetch(query, rule_id, limit)
            return [Alert.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch alerts for rule {rule_id}: {e}")
            raise

    async def get_by_user(self, user_id: int, limit: int = 20) -> List[Alert]:
        """
        Получает последние алерты пользователя.

        Args:
            user_id: ID пользователя
            limit: Максимальное количество результатов
        """
        query = """
            SELECT * FROM alerts
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        try:
            rows = await self.db.pool.fetch(query, user_id, limit)
            return [Alert.from_db_row(dict(row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch alerts for user {user_id}: {e}")
            raise

    async def mark_as_sent(self, alert_id: int) -> None:
        """Отмечает алерт как отправленный."""
        query = "UPDATE alerts SET sent_at = $1 WHERE id = $2"
        try:
            await self.db.pool.execute(query, datetime.utcnow(), alert_id)
            logger.info(f"Alert {alert_id} marked as sent")
        except Exception as e:
            logger.error(f"Failed to mark alert as sent: {e}")
            raise

    async def lot_already_alerted(self, rule_id: int, lot_id: str) -> bool:
        """
        Проверяет, был ли уже отправлен алерт по этому лоту для данного правила.

        Args:
            rule_id: ID правила
            lot_id: ID лота

        Returns:
            True если алерт уже существует
        """
        query = "SELECT COUNT(*) FROM alerts WHERE rule_id = $1 AND lot_id = $2"
        try:
            count = await self.db.pool.fetchval(query, rule_id, lot_id)
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check if lot was alerted: {e}")
            raise

    async def delete_old_alerts(self, days: int = 30) -> int:
        """
        Удаляет старые алерты.

        Args:
            days: Количество дней, после которых алерты считаются старыми

        Returns:
            Количество удаленных алертов
        """
        query = """
            DELETE FROM alerts
            WHERE created_at < NOW() - INTERVAL '%s days'
        """
        try:
            result = await self.db.pool.execute(query % days)
            # Извлекаем количество из строки типа "DELETE 5"
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Deleted {count} old alerts (older than {days} days)")
            return count
        except Exception as e:
            logger.error(f"Failed to delete old alerts: {e}")
            raise