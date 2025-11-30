"""Сервис для работы с Portals API."""

import logging
from typing import List, Optional, Dict, Any
from aportalsmp import update_auth, search, filterFloors, collections
from src.config import get_settings
from src.models import Gift

logger = logging.getLogger(__name__)


class PortalsService:
    """Сервис для взаимодействия с Portals Marketplace API."""

    def __init__(self):
        self.settings = get_settings()
        self._auth_token: Optional[str] = None

    async def init_auth(self) -> None:
        """Инициализирует аутентификацию с Portals API."""
        try:
            self._auth_token = await update_auth(self.settings.api_id, self.settings.api_hash)
            logger.info("Portals API authentication successful")
        except Exception as e:
            logger.error(f"Failed to authenticate with Portals API: {e}")
            raise

    async def refresh_auth(self) -> None:
        """Обновляет токен аутентификации."""
        await self.init_auth()

    async def search_gift(
        self, gift_name: str, model: Optional[str] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Ищет подарки в Portals API.

        Args:
            gift_name: Название подарка
            model: Модель подарка (опционально)
            limit: Максимальное количество результатов

        Returns:
            Список найденных подарков
        """
        if not self._auth_token:
            await self.init_auth()

        try:
            result = await search(
                gift_name=[gift_name],
                model=[model] if model else [],
                limit=limit,
                sort="price_asc",
                authData=self._auth_token,
            )

            if isinstance(result, dict) and "items" in result:
                return result["items"]
            elif isinstance(result, list):
                return result
            else:
                logger.warning(f"Unexpected API response format: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"Error searching for gift '{gift_name}': {e}")
            if "auth" in str(e).lower():
                await self.refresh_auth()
            raise

    async def get_gift_data(self, gift_name: str, model: str, user_id: int) -> Optional[Gift]:
        """
        Получает данные о подарке и создает объект Gift.

        Args:
            gift_name: Название подарка
            model: Модель подарка
            user_id: ID пользователя

        Returns:
            Объект Gift или None если не найден
        """
        try:
            items = await self.search_gift(gift_name, model, limit=1)

            if not items:
                logger.warning(f"Gift '{gift_name}' ({model}) not found")
                return None

            return Gift.from_api_response(items[0], user_id, model)

        except Exception as e:
            logger.error(f"Error getting gift data: {e}")
            return None

    async def collections(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает список коллекций из Portals API.

        Args:
            limit: Максимальное количество коллекций

        Returns:
            Список коллекций
        """
        if not self._auth_token:
            await self.init_auth()

        try:
            result = await collections(limit=limit, authData=self._auth_token)

            # API возвращает объект Collections с атрибутом _collections
            if hasattr(result, '_collections'):
                colls = getattr(result, '_collections')
                if isinstance(colls, list):
                    return colls

            # Fallback на старый формат
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            if "auth" in str(e).lower():
                await self.refresh_auth()
            raise

    async def filterFloors(self, gift_name: str = "") -> Dict[str, Any]:
        """
        Получает floor данные для коллекции.

        Args:
            gift_name: Название коллекции

        Returns:
            Словарь с floor данными (models, backdrops, symbols)
        """
        if not self._auth_token:
            await self.init_auth()

        try:
            result = await filterFloors(gift_name=gift_name, authData=self._auth_token)

            # API возвращает объект Filters с атрибутами models, backdrops, symbols
            if hasattr(result, 'models') or hasattr(result, 'backdrops') or hasattr(result, 'symbols'):
                return {
                    'models': getattr(result, 'models', {}),
                    'backdrops': getattr(result, 'backdrops', {}),
                    'symbols': getattr(result, 'symbols', {}),
                }

            # Fallback на старый формат
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.error(f"Error getting floors for '{gift_name}': {e}")
            if "auth" in str(e).lower():
                await self.refresh_auth()
            raise

    async def search(
        self,
        sort: str = "price_asc",
        offset: int = 0,
        limit: int = 20,
        gift_name: str = "",
        model: str = "",
        min_price: int = 0,
        max_price: int = 100000,
    ) -> List[Dict[str, Any]]:
        """
        Поиск лотов в Portals API.

        Args:
            sort: Сортировка (price_asc, price_desc, latest)
            offset: Смещение для пагинации
            limit: Количество результатов
            gift_name: Название коллекции (фильтр)
            model: Модель (фильтр)
            min_price: Минимальная цена
            max_price: Максимальная цена

        Returns:
            Список найденных лотов
        """
        if not self._auth_token:
            await self.init_auth()

        try:
            result = await search(
                sort=sort,
                offset=offset,
                limit=limit,
                gift_name=[gift_name] if gift_name else [],
                model=[model] if model else [],
                min_price=min_price,
                max_price=max_price,
                authData=self._auth_token,
            )

            # Конвертируем PortalsGift объекты в словари
            items = []
            if isinstance(result, dict) and "items" in result:
                items = result["items"]
            elif isinstance(result, list):
                items = result

            # Преобразуем объекты в словари
            converted_items = []
            for item in items:
                if hasattr(item, '__dict__'):
                    # Если это объект, берём его атрибуты
                    item_dict = {
                        'id': getattr(item, 'id', ''),
                        'name': getattr(item, 'name', ''),
                        'model': getattr(item, 'model', ''),
                        'price': getattr(item, 'price', 0),
                        'floor_price': getattr(item, 'floor_price', 0),
                        'photo_url': getattr(item, 'photo_url', ''),
                    }
                    converted_items.append(item_dict)
                elif isinstance(item, dict):
                    # Если уже словарь, оставляем как есть
                    converted_items.append(item)

            return converted_items

        except Exception as e:
            logger.error(f"Error searching lots: {e}")
            if "auth" in str(e).lower():
                await self.refresh_auth()
            raise