"""Парсинг ссылок на подарки из Portals."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse_portals_link(text: str) -> Optional[str]:
    """
    Извлекает gift_id из ссылки Portals.

    Примеры ссылок:
    - https://t.me/portals/market?startapp=gift_bb8a2602-240d-4234-94f1-e8180cc6e454_k74zqq
    - t.me/portals/market?startapp=gift_abc123_xyz

    Args:
        text: Текст сообщения, возможно содержащий ссылку

    Returns:
        gift_id или None если ссылка не найдена
    """
    # Паттерн для ссылок Portals
    patterns = [
        r'(?:https?://)?t\.me/portals/market\?startapp=gift_([a-zA-Z0-9_-]+)',
        r'startapp=gift_([a-zA-Z0-9_-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            gift_id = match.group(1)
            logger.info(f"Extracted gift_id from link: {gift_id}")
            return gift_id

    logger.debug("No Portals gift link found in text")
    return None


def is_portals_link(text: str) -> bool:
    """Проверяет, содержит ли текст ссылку на Portals."""
    return parse_portals_link(text) is not None