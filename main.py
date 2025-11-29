"""">G:0 2E>40 2 ?@8;>65=85."""

import asyncio
import logging

from src.config import get_settings
from src.database import get_db_connection, init_database
from src.bot import create_bot, create_dispatcher
from src.services import PriceTracker, TrackingPriceTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """;02=0O DC=:F8O 70?CA:0 ?@8;>65=8O."""
    logger.info("Starting Portals Price Tracker Bot...")

    settings = get_settings()
    logger.info(f"Loaded settings: DB={settings.db_name}@{settings.db_host}:{settings.db_port}")

    db = get_db_connection()
    await db.connect()
    logger.info("Database connected")

    await init_database()
    logger.info("Database initialized")

    bot = create_bot()
    dp = create_dispatcher()

    # Запускаем старый price tracker (legacy для gifts)
    price_tracker = PriceTracker(bot)
    asyncio.create_task(price_tracker.start())
    logger.info("Legacy price tracker started")

    # Запускаем новый tracking price tracker (для правил отслеживания)
    tracking_tracker = TrackingPriceTracker(bot)
    asyncio.create_task(tracking_tracker.start())
    logger.info("Tracking price tracker started")

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        price_tracker.stop()
        tracking_tracker.stop()
        await db.disconnect()
        await bot.session.close()
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")