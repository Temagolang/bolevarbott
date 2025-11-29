"""Модель алерта (уведомления о найденном лоте)."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Alert:
    """Уведомление о найденном лоте, соответствующем правилу."""

    rule_id: int
    user_id: int
    lot_id: str
    lot_price: float
    lot_floor_price: float
    collection_name: str
    model: str
    alert_id: Optional[int] = None
    photo_url: Optional[str] = None
    lot_url: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict) -> "Alert":
        """Создает объект Alert из строки БД."""
        return cls(
            alert_id=row["id"],
            rule_id=row["rule_id"],
            user_id=row["user_id"],
            lot_id=row["lot_id"],
            lot_price=float(row["lot_price"]),
            lot_floor_price=float(row["lot_floor_price"]),
            collection_name=row["collection_name"],
            model=row["model"],
            photo_url=row.get("photo_url"),
            lot_url=row.get("lot_url"),
            sent_at=row.get("sent_at"),
            created_at=row.get("created_at"),
        )

    def format_message(self) -> str:
        """Форматирует сообщение алерта для отправки пользователю."""
        message = "🔔 Найден подходящий лот\n\n"
        message += f"Коллекция: **{self.collection_name}**\n"
        message += f"Модель: **{self.model}**\n\n"
        message += f"Цена: **{self.lot_price} TON**\n"
        message += f"Floor по коллекции: **{self.lot_floor_price} TON**\n"

        # Вычисляем скидку от floor
        if self.lot_floor_price > 0:
            discount = ((self.lot_floor_price - self.lot_price) / self.lot_floor_price) * 100
            if discount > 0:
                message += f"Скидка: **{discount:.1f}%** от floor\n"

        message += f"\n(удовлетворяет правилу #{self.rule_id})"

        return message