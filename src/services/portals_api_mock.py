"""Моки для Portals Marketplace API на время разработки."""

import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Моковые коллекции
MOCK_COLLECTIONS = [
    {
        "name": "Toy Bear",
        "floor_price": 40.0,
        "volume_24h": 1250.5,
        "total_items": 15000,
    },
    {
        "name": "Pumpkin Cat",
        "floor_price": 25.0,
        "volume_24h": 890.3,
        "total_items": 8500,
    },
    {
        "name": "Hedgehog",
        "floor_price": 15.0,
        "volume_24h": 450.2,
        "total_items": 5200,
    },
    {
        "name": "Crystal Ball",
        "floor_price": 60.0,
        "volume_24h": 2100.7,
        "total_items": 3200,
    },
    {
        "name": "Dragon Statue",
        "floor_price": 120.0,
        "volume_24h": 5500.0,
        "total_items": 1800,
    },
]

# Моковые модели для каждой коллекции
MOCK_MODELS_FLOORS = {
    "Toy Bear": {
        "models": {
            "Wizard": 45.0,
            "Knight": 38.0,
            "Witch": 42.0,
            "Pirate": 35.0,
            "King": 55.0,
        },
        "backdrops": {
            "Forest": 30.0,
            "Castle": 50.0,
            "Ocean": 35.0,
        },
        "symbols": {
            "Star": 32.0,
            "Moon": 38.0,
            "Sun": 45.0,
        },
    },
    "Pumpkin Cat": {
        "models": {
            "Classic": 20.0,
            "Scary": 28.0,
            "Cute": 22.0,
            "Vampire": 35.0,
        },
        "backdrops": {
            "Night": 18.0,
            "Halloween": 30.0,
        },
        "symbols": {
            "Bat": 15.0,
            "Ghost": 20.0,
        },
    },
    "Hedgehog": {
        "models": {
            "Blue": 12.0,
            "Pink": 15.0,
            "Green": 13.0,
            "Gold": 25.0,
        },
        "backdrops": {
            "Garden": 10.0,
            "Space": 18.0,
        },
        "symbols": {
            "Flower": 8.0,
            "Star": 12.0,
        },
    },
    "Crystal Ball": {
        "models": {
            "Clear": 55.0,
            "Purple": 65.0,
            "Rainbow": 75.0,
        },
        "backdrops": {
            "Mystic": 50.0,
            "Galaxy": 70.0,
        },
        "symbols": {
            "Moon": 60.0,
            "Eye": 65.0,
        },
    },
    "Dragon Statue": {
        "models": {
            "Fire": 100.0,
            "Ice": 110.0,
            "Lightning": 130.0,
            "Shadow": 150.0,
        },
        "backdrops": {
            "Mountain": 90.0,
            "Sky": 120.0,
        },
        "symbols": {
            "Flame": 100.0,
            "Thunder": 115.0,
        },
    },
}

# Счетчик для генерации ID
_lot_counter = 1000


def _generate_lot_id() -> str:
    """Генерирует уникальный ID лота."""
    global _lot_counter
    _lot_counter += 1
    return f"gift_{_lot_counter:08d}_mock"


# Генерируем моковые лоты
def _generate_mock_lots() -> List[Dict[str, Any]]:
    """Генерирует список моковых лотов на рынке."""
    lots = []

    for collection in MOCK_COLLECTIONS:
        collection_name = collection["name"]
        if collection_name not in MOCK_MODELS_FLOORS:
            continue

        models_data = MOCK_MODELS_FLOORS[collection_name]

        # Генерируем несколько лотов для каждой модели
        for model, floor_price in models_data["models"].items():
            # Лоты с разными ценами относительно floor
            prices = [
                floor_price * 0.85,  # -15% от floor
                floor_price * 0.95,  # -5% от floor
                floor_price * 1.0,   # floor
                floor_price * 1.1,   # +10% от floor
                floor_price * 1.2,   # +20% от floor
            ]

            for price in prices:
                lot = {
                    "id": _generate_lot_id(),
                    "tg_id": 123456789,  # Mock telegram ID
                    "collection_id": f"col_{collection_name.lower().replace(' ', '_')}",
                    "name": collection_name,
                    "model": model,
                    "model_rarity": _get_random_rarity(),
                    "price": round(price, 2),
                    "floor_price": collection["floor_price"],  # Floor всей коллекции
                    "photo_url": f"https://example.com/photos/{collection_name.lower()}_{model.lower()}.jpg",
                    "animation_url": None,
                    "symbol": list(models_data["symbols"].keys())[0],
                    "symbol_rarity": _get_random_rarity(),
                    "backdrop": list(models_data["backdrops"].keys())[0],
                    "backdrop_rarity": _get_random_rarity(),
                    "listed_at": "2024-11-28T12:00:00Z",
                    "status": "listed",
                    "emoji_id": _get_emoji(collection_name),
                    "unlocks_at": None,
                }
                lots.append(lot)

    return lots


def _get_random_rarity() -> str:
    """Возвращает случайную редкость."""
    import random
    return random.choice(["Common", "Rare", "Epic", "Legendary"])


def _get_emoji(collection_name: str) -> str:
    """Возвращает эмодзи для коллекции."""
    emojis = {
        "Toy Bear": "🧸",
        "Pumpkin Cat": "🎃",
        "Hedgehog": "🦔",
        "Crystal Ball": "🔮",
        "Dragon Statue": "🐉",
    }
    return emojis.get(collection_name, "🎁")


# Генерируем лоты при импорте модуля
MOCK_LOTS = _generate_mock_lots()


class MockPortalsAPI:
    """Мок Portals Marketplace API для разработки."""

    def __init__(self):
        self._auth_token: Optional[str] = None

    async def update_auth(self, api_id: int, api_hash: str) -> str:
        """Мок аутентификации."""
        logger.info(f"🔐 MOCK: Authenticating with API_ID={api_id}")
        await asyncio.sleep(0.1)  # Имитация запроса
        self._auth_token = f"mock_token_{api_id}_{api_hash[:8]}"
        return self._auth_token

    async def collections(self, limit: int = 100, authData: str = "") -> List[Dict[str, Any]]:
        """Возвращает список коллекций."""
        logger.info(f"📚 MOCK: Getting collections (limit={limit})")
        await asyncio.sleep(0.05)
        return MOCK_COLLECTIONS[:limit]

    async def filterFloors(self, gift_name: str = "", authData: str = "") -> Dict[str, Any]:
        """Возвращает floor данные для коллекции."""
        logger.info(f"📊 MOCK: Getting floors for '{gift_name}'")
        await asyncio.sleep(0.05)

        if gift_name in MOCK_MODELS_FLOORS:
            return MOCK_MODELS_FLOORS[gift_name]

        # Если коллекция не найдена
        return {"models": {}, "backdrops": {}, "symbols": {}}

    async def search(
        self,
        sort: str = "price_asc",
        offset: int = 0,
        limit: int = 20,
        gift_name: str | List[str] = "",
        model: str | List[str] = "",
        backdrop: str | List[str] = "",
        symbol: str | List[str] = "",
        min_price: int = 0,
        max_price: int = 100000,
        authData: str = "",
    ) -> List[Dict[str, Any]]:
        """Поиск подарков с фильтрацией."""
        logger.info(f"🔍 MOCK: Searching gifts (name={gift_name}, model={model}, max_price={max_price})")
        await asyncio.sleep(0.1)

        # Нормализуем входные данные
        if isinstance(gift_name, str):
            gift_names = [gift_name] if gift_name else []
        else:
            gift_names = gift_name

        if isinstance(model, str):
            models = [model] if model else []
        else:
            models = model

        # Фильтруем лоты
        results = []
        for lot in MOCK_LOTS:
            # Фильтр по названию
            if gift_names and lot["name"] not in gift_names:
                continue

            # Фильтр по модели
            if models and lot["model"] not in models:
                continue

            # Фильтр по цене
            if lot["price"] < min_price or lot["price"] > max_price:
                continue

            results.append(lot)

        # Сортировка
        if sort == "price_asc":
            results.sort(key=lambda x: x["price"])
        elif sort == "price_desc":
            results.sort(key=lambda x: x["price"], reverse=True)
        elif sort == "latest":
            results.sort(key=lambda x: x["listed_at"], reverse=True)

        # Пагинация
        paginated = results[offset : offset + limit]

        logger.info(f"✅ MOCK: Found {len(paginated)} lots (total matching: {len(results)})")
        return paginated


# Singleton instance
_mock_api_instance: Optional[MockPortalsAPI] = None


def get_mock_api() -> MockPortalsAPI:
    """Возвращает singleton мок API."""
    global _mock_api_instance
    if _mock_api_instance is None:
        _mock_api_instance = MockPortalsAPI()
    return _mock_api_instance