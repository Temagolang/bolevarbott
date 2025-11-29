"""Сервис для отслеживания цен на подарки."""

import asyncio
import logging
from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.config import get_settings
from src.repositories import GiftRepository
from src.services.portals_service import PortalsService
from src.models import Gift

logger = logging.getLogger(__name__)


class PriceTracker:
    """Сервис для мониторинга цен на подарки."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings = get_settings()
        self.gift_repo = GiftRepository()
        self.portals_service = PortalsService()
        self._running = False

    async def check_prices(self) -> None:
        """Проверяет цены на все отслеживаемые подарки."""
        try:
            gifts = await self.gift_repo.get_all()
            logger.info(f"Checking prices for {len(gifts)} gifts")

            for gift in gifts:
                await self._check_gift_price(gift)

        except Exception as e:
            logger.error(f"Error in check_prices: {e}", exc_info=True)

    async def _check_gift_price(self, gift: Gift) -> None:
        """Проверяет цену конкретного подарка."""
        if not gift.model:
            logger.warning(f"Skipping gift '{gift.name}' for user {gift.user_id} (no model)")
            return

        try:
            updated_gift = await self.portals_service.get_gift_data(
                gift.name, gift.model, gift.user_id
            )

            if not updated_gift:
                logger.warning(f"Could not fetch data for '{gift.name}' ({gift.model})")
                return

            if updated_gift.price < gift.price or updated_gift.floor_price < gift.floor_price:
                await self._send_price_alert(gift, updated_gift)
                await self.gift_repo.update_prices(
                    gift.user_id,
                    gift.name,
                    gift.model,
                    updated_gift.price,
                    updated_gift.floor_price,
                )

        except Exception as e:
            logger.error(
                f"Error checking price for '{gift.name}' ({gift.model}): {e}",
                exc_info=True,
            )

    async def _send_price_alert(self, old_gift: Gift, new_gift: Gift) -> None:
        """Отправляет уведомление о снижении цены."""
        caption = (
            f"🎁 Обнаружено снижение цены!\n\n"
            f"Подарок: {new_gift.name} ({new_gift.model})\n"
            f"Цена: {old_gift.price} → {new_gift.price}\n"
            f"Флор: {old_gift.floor_price} → {new_gift.floor_price}"
        )

        keyboard = None
        if new_gift.gift_id:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Открыть в Portals",
                            url=f"https://t.me/portals/market?startapp=gift_{new_gift.gift_id}",
                        )
                    ]
                ]
            )

        try:
            if new_gift.photo_url:
                await self.bot.send_photo(
                    chat_id=new_gift.user_id,
                    photo=new_gift.photo_url,
                    caption=caption,
                    reply_markup=keyboard,
                )
            else:
                await self.bot.send_message(
                    chat_id=new_gift.user_id, text=caption, reply_markup=keyboard
                )
            logger.info(f"Price alert sent to user {new_gift.user_id}")
        except Exception as e:
            logger.error(f"Failed to send price alert to user {new_gift.user_id}: {e}")

    async def start(self) -> None:
        """Запускает мониторинг цен."""
        if self._running:
            logger.warning("Price tracker is already running")
            return

        self._running = True
        logger.info("Price tracker started")

        await self.portals_service.init_auth()

        while self._running:
            try:
                await self.check_prices()
            except Exception as e:
                logger.error(f"Error in price tracker loop: {e}", exc_info=True)

            await asyncio.sleep(self.settings.price_check_interval)

    def stop(self) -> None:
        """Останавливает мониторинг цен."""
        self._running = False
        logger.info("Price tracker stopped")