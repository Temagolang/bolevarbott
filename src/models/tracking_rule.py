"""Модель правила отслеживания цен."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum


class ConditionType(str, Enum):
    """Типы условий для отслеживания цен."""

    FIXED_PRICE = "fixed_price"  # Фиксированная цена (≤ X TON)
    FLOOR_DISCOUNT = "floor_discount"  # Скидка к floor (ниже пола на X%)
    ANY_PRICE = "any_price"  # Любая цена (просто уведомлять о новых лотах)


@dataclass
class TrackingRule:
    """Правило отслеживания цен на подарки в Portals."""

    user_id: int
    collection_name: str
    condition_type: ConditionType
    is_active: bool = True
    model: Optional[str] = None
    target_price: Optional[float] = None  # Для FIXED_PRICE
    floor_discount_percent: Optional[int] = None  # Для FLOOR_DISCOUNT
    rule_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: dict) -> "TrackingRule":
        """Создает объект TrackingRule из строки БД."""
        return cls(
            rule_id=row["id"],
            user_id=row["user_id"],
            collection_name=row["collection_name"],
            model=row.get("model"),
            condition_type=ConditionType(row["condition_type"]),
            target_price=float(row["target_price"]) if row.get("target_price") else None,
            floor_discount_percent=row.get("floor_discount_percent"),
            is_active=row["is_active"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def matches_lot(self, lot_price: float, floor_price: float) -> bool:
        """
        Проверяет, соответствует ли лот условиям правила.

        Args:
            lot_price: Цена лота
            floor_price: Floor price модели

        Returns:
            True если лот подходит под условия
        """
        if self.condition_type == ConditionType.ANY_PRICE:
            return True

        if self.condition_type == ConditionType.FIXED_PRICE:
            if self.target_price is None:
                return False
            return lot_price <= self.target_price

        if self.condition_type == ConditionType.FLOOR_DISCOUNT:
            if self.floor_discount_percent is None or floor_price == 0:
                return False
            threshold = floor_price * (1 - self.floor_discount_percent / 100)
            return lot_price <= threshold

        return False

    def get_description(self) -> str:
        """Возвращает текстовое описание правила для UI."""
        parts = [f"Коллекция: {self.collection_name}"]

        if self.model:
            parts.append(f"Модель: {self.model}")
        else:
            parts.append("Модель: любая")

        if self.condition_type == ConditionType.FIXED_PRICE:
            parts.append(f"Цена ≤ {self.target_price} TON")
        elif self.condition_type == ConditionType.FLOOR_DISCOUNT:
            parts.append(f"Ниже floor на {self.floor_discount_percent}%")
        elif self.condition_type == ConditionType.ANY_PRICE:
            parts.append("Любая цена")

        status = "✅ активно" if self.is_active else "⏸ на паузе"
        parts.append(f"Статус: {status}")

        return "\n".join(parts)