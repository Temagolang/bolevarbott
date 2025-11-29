"""Модели данных для подарков."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Gift:
    """Модель подарка для отслеживания цен."""

    name: str
    model: str
    price: float
    floor_price: float
    user_id: int
    photo_url: Optional[str] = None
    model_rarity: Optional[str] = None
    gift_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_api_response(cls, data: dict, user_id: int, model: str) -> "Gift":
        """Создает объект Gift из ответа Portals API."""
        return cls(
            name=data.get("name", ""),
            model=model,
            price=float(data.get("price", 0)),
            floor_price=float(data.get("floor_price", 0)),
            user_id=user_id,
            photo_url=data.get("photo_url"),
            model_rarity=data.get("model_rarity"),
            gift_id=data.get("id"),
        )

    @classmethod
    def from_db_row(cls, row: dict) -> "Gift":
        """Создает объект Gift из строки БД."""
        return cls(
            name=row["name"],
            model=row["model"],
            price=float(row["price"]),
            floor_price=float(row["floor_price"]),
            user_id=row["user_id"],
            photo_url=row.get("photo_url"),
            model_rarity=row.get("model_rarity"),
            gift_id=row.get("gift_id"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )