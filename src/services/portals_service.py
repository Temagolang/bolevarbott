"""Сервис для работы с Portals API."""

import logging
from typing import List, Optional, Dict, Any
from aportalsmp import update_auth, search
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