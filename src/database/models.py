"""SQL схемы и инициализация базы данных PostgreSQL."""

import logging
from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)


CREATE_GIFTS_TABLE = """
CREATE TABLE IF NOT EXISTS gifts (
    name VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) DEFAULT 0,
    floor_price DECIMAL(10, 2) DEFAULT 0,
    photo_url TEXT,
    model_rarity VARCHAR(50),
    gift_id VARCHAR(255),
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, name, model)
);
"""

CREATE_TRACKING_RULES_TABLE = """
CREATE TABLE IF NOT EXISTS tracking_rules (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    model VARCHAR(255),
    condition_type VARCHAR(50) NOT NULL,
    target_price DECIMAL(10, 2),
    floor_discount_percent INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_condition_type CHECK (
        condition_type IN ('fixed_price', 'floor_discount', 'any_price')
    )
);
"""

CREATE_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL,
    user_id BIGINT NOT NULL,
    lot_id VARCHAR(255) NOT NULL,
    lot_price DECIMAL(10, 2) NOT NULL,
    lot_floor_price DECIMAL(10, 2) NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    photo_url TEXT,
    lot_url TEXT,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES tracking_rules(id) ON DELETE CASCADE
);
"""

CREATE_UPDATED_AT_TRIGGER = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_gifts_updated_at ON gifts;
DROP TRIGGER IF EXISTS update_tracking_rules_updated_at ON tracking_rules;

CREATE TRIGGER update_gifts_updated_at
    BEFORE UPDATE ON gifts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tracking_rules_updated_at
    BEFORE UPDATE ON tracking_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""


async def init_database() -> None:
    """Инициализирует структуру базы данных."""
    db = get_db_connection()
    pool = db.pool

    async with pool.acquire() as conn:
        try:
            await conn.execute(CREATE_GIFTS_TABLE)
            await conn.execute(CREATE_TRACKING_RULES_TABLE)
            await conn.execute(CREATE_ALERTS_TABLE)
            await conn.execute(CREATE_UPDATED_AT_TRIGGER)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise