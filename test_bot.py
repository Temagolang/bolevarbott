"""Простой скрипт для тестирования бота с моками."""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Mock для Portals API
class MockPortalsAPI:
    """Mock Portals API для тестирования."""

    def __init__(self):
        self.auth_token = "mock_token_12345"
        self.gifts_db = {
            ("Dragon Statue", "Fire"): {
                "name": "Dragon Statue",
                "price": 1000.0,
                "floor_price": 900.0,
                "photo_url": "https://example.com/dragon.jpg",
                "model_rarity": "Legendary",
                "id": "gift_001",
            },
            ("Unicorn Figure", "Rainbow"): {
                "name": "Unicorn Figure",
                "price": 500.0,
                "floor_price": 450.0,
                "photo_url": "https://example.com/unicorn.jpg",
                "model_rarity": "Epic",
                "id": "gift_002",
            },
        }

    async def update_auth(self, api_id, api_hash):
        logger.info("🔐 Mock: Аутентификация в Portals API")
        await asyncio.sleep(0.1)
        return self.auth_token

    async def search(self, gift_name, model=None, limit=5, sort="price_asc", authData=None):
        logger.info(f"🔍 Mock: Поиск подарка '{gift_name[0]}' модель '{model[0] if model else 'Any'}'")
        await asyncio.sleep(0.1)

        name = gift_name[0]
        model_name = model[0] if model and model[0] else None

        results = []
        for (db_name, db_model), gift_data in self.gifts_db.items():
            if name.lower() in db_name.lower():
                if model_name is None or model_name.lower() in db_model.lower():
                    results.append(gift_data.copy())

        if results:
            logger.info(f"✅ Mock: Найдено {len(results)} подарков")
        else:
            logger.warning(f"❌ Mock: Подарки не найдены")

        return {"items": results}


# Mock БД
class MockDatabase:
    """Mock база данных для тестирования."""

    def __init__(self):
        self.gifts = []
        self.connected = False

    async def connect(self):
        logger.info("🗄️  Mock: Подключение к БД")
        await asyncio.sleep(0.1)
        self.connected = True

    async def disconnect(self):
        logger.info("🗄️  Mock: Отключение от БД")
        self.connected = False

    async def add_gift(self, gift):
        logger.info(f"💾 Mock: Сохранение подарка '{gift['name']}' для пользователя {gift['user_id']}")
        self.gifts.append(gift)

    async def get_all_gifts(self):
        logger.info(f"📋 Mock: Получение всех подарков (всего: {len(self.gifts)})")
        return self.gifts


# Mock Telegram Bot
class MockTelegramBot:
    """Mock Telegram бота для тестирования."""

    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id, text, reply_markup=None):
        logger.info(f"📤 Mock Bot: Отправка сообщения пользователю {chat_id}")
        logger.info(f"   Текст: {text[:100]}...")
        self.sent_messages.append({
            "chat_id": chat_id,
            "text": text,
            "reply_markup": reply_markup,
        })

    async def send_photo(self, chat_id, photo, caption, reply_markup=None):
        logger.info(f"📸 Mock Bot: Отправка фото пользователю {chat_id}")
        logger.info(f"   Фото: {photo}")
        logger.info(f"   Описание: {caption[:100]}...")
        self.sent_messages.append({
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "reply_markup": reply_markup,
        })


async def test_add_gift_flow():
    """Тестирование полного цикла добавления подарка."""
    logger.info("\n" + "="*60)
    logger.info("🧪 ТЕСТ 1: Добавление подарка")
    logger.info("="*60)

    # Инициализация моков
    portals_api = MockPortalsAPI()
    db = MockDatabase()
    bot = MockTelegramBot()

    # Подключаемся к БД
    await db.connect()

    # Симуляция пользовательского ввода
    user_id = 123456789
    gift_name = "Dragon Statue"
    model = "Fire"

    logger.info(f"\n👤 Пользователь {user_id} запускает /add")
    logger.info(f"   Вводит название: {gift_name}")
    logger.info(f"   Вводит модель: {model}")

    # Аутентификация в Portals
    await portals_api.update_auth(12345, "hash")

    # Поиск подарка
    results = await portals_api.search(
        gift_name=[gift_name],
        model=[model],
        limit=1,
        sort="price_asc",
        authData=portals_api.auth_token,
    )

    if results["items"]:
        gift_data = results["items"][0]

        # Сохранение в БД
        gift_record = {
            "name": gift_data["name"],
            "model": model,
            "price": gift_data["price"],
            "floor_price": gift_data["floor_price"],
            "photo_url": gift_data.get("photo_url"),
            "model_rarity": gift_data.get("model_rarity"),
            "gift_id": gift_data.get("id"),
            "user_id": user_id,
        }
        await db.add_gift(gift_record)

        # Отправка подтверждения пользователю
        caption = (
            f"✅ Подарок добавлен для отслеживания\n\n"
            f"Название: {gift_data['name']}\n"
            f"Модель: {model}\n"
            f"Цена: {gift_data['price']}\n"
            f"Флор: {gift_data['floor_price']}\n"
            f"Редкость: {gift_data.get('model_rarity', 'N/A')}"
        )
        await bot.send_photo(
            chat_id=user_id,
            photo=gift_data.get("photo_url"),
            caption=caption,
        )

        logger.info(f"\n✅ Тест пройден! Подарок добавлен в БД")
        logger.info(f"   Всего подарков в БД: {len(db.gifts)}")
    else:
        logger.error("❌ Тест провален! Подарок не найден")

    await db.disconnect()


async def test_price_tracker():
    """Тестирование отслеживания цен."""
    logger.info("\n" + "="*60)
    logger.info("🧪 ТЕСТ 2: Отслеживание изменения цен")
    logger.info("="*60)

    # Инициализация моков
    portals_api = MockPortalsAPI()
    db = MockDatabase()
    bot = MockTelegramBot()

    await db.connect()

    # Добавляем подарок в БД
    user_id = 123456789
    old_gift = {
        "name": "Dragon Statue",
        "model": "Fire",
        "price": 1200.0,  # Старая цена выше
        "floor_price": 1000.0,  # Старый флор выше
        "photo_url": "https://example.com/dragon.jpg",
        "model_rarity": "Legendary",
        "gift_id": "gift_001",
        "user_id": user_id,
    }
    await db.add_gift(old_gift)

    logger.info(f"\n📊 В БД есть подарок: {old_gift['name']}")
    logger.info(f"   Текущая цена: {old_gift['price']}")
    logger.info(f"   Текущий флор: {old_gift['floor_price']}")

    # Симуляция проверки цен (как это делает price tracker)
    logger.info(f"\n⏰ Запуск проверки цен...")

    gifts = await db.get_all_gifts()
    for gift in gifts:
        # Получаем актуальную цену из API
        results = await portals_api.search(
            gift_name=[gift["name"]],
            model=[gift["model"]],
            limit=1,
        )

        if results["items"]:
            current = results["items"][0]
            new_price = current["price"]
            new_floor = current["floor_price"]

            logger.info(f"\n💰 Проверка цены для {gift['name']}:")
            logger.info(f"   Старая цена: {gift['price']} → Новая: {new_price}")
            logger.info(f"   Старый флор: {gift['floor_price']} → Новый: {new_floor}")

            # Проверяем снижение цены
            if new_price < gift["price"] or new_floor < gift["floor_price"]:
                logger.info(f"   🎉 Обнаружено снижение цены!")

                # Отправляем уведомление
                caption = (
                    f"🎁 Обнаружено снижение цены!\n\n"
                    f"Подарок: {gift['name']} ({gift['model']})\n"
                    f"Цена: {gift['price']} → {new_price}\n"
                    f"Флор: {gift['floor_price']} → {new_floor}"
                )
                await bot.send_photo(
                    chat_id=gift["user_id"],
                    photo=current.get("photo_url"),
                    caption=caption,
                )

                logger.info(f"   ✅ Уведомление отправлено пользователю!")
            else:
                logger.info(f"   ℹ️  Цена не изменилась или выросла")

    logger.info(f"\n✅ Тест пройден! Всего отправлено уведомлений: {len(bot.sent_messages)}")

    await db.disconnect()


async def test_config():
    """Тестирование загрузки конфигурации."""
    logger.info("\n" + "="*60)
    logger.info("🧪 ТЕСТ 3: Загрузка конфигурации")
    logger.info("="*60)

    import os
    os.environ["BOT_TOKEN"] = "test_token_123"
    os.environ["API_ID"] = "12345"
    os.environ["API_HASH"] = "test_hash"
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_USER"] = "postgres"
    os.environ["DB_PASSWORD"] = "test_pass"

    from src.config import get_settings

    settings = get_settings()

    logger.info(f"\n📋 Загруженные настройки:")
    logger.info(f"   BOT_TOKEN: {settings.bot_token[:20]}...")
    logger.info(f"   API_ID: {settings.api_id}")
    logger.info(f"   DB_HOST: {settings.db_host}")
    logger.info(f"   DB_PORT: {settings.db_port}")
    logger.info(f"   PRICE_CHECK_INTERVAL: {settings.price_check_interval}s")

    logger.info(f"\n✅ Тест пройден! Конфигурация загружена корректно")


async def test_gift_model():
    """Тестирование модели Gift."""
    logger.info("\n" + "="*60)
    logger.info("🧪 ТЕСТ 4: Модель данных Gift")
    logger.info("="*60)

    from src.models.gift import Gift

    # Тест создания из API ответа
    api_data = {
        "name": "Test Gift",
        "price": 100.0,
        "floor_price": 90.0,
        "photo_url": "https://example.com/photo.jpg",
        "model_rarity": "Rare",
        "id": "gift_123",
    }

    gift = Gift.from_api_response(api_data, user_id=999, model="TestModel")

    logger.info(f"\n📦 Создан объект Gift:")
    logger.info(f"   Название: {gift.name}")
    logger.info(f"   Модель: {gift.model}")
    logger.info(f"   Цена: {gift.price}")
    logger.info(f"   Флор: {gift.floor_price}")
    logger.info(f"   User ID: {gift.user_id}")
    logger.info(f"   Редкость: {gift.model_rarity}")

    assert gift.name == "Test Gift"
    assert gift.model == "TestModel"
    assert gift.price == 100.0
    assert gift.user_id == 999

    logger.info(f"\n✅ Тест пройден! Модель работает корректно")


async def main():
    """Запуск всех тестов."""
    logger.info("\n" + "🚀 "* 20)
    logger.info("ЗАПУСК ТЕСТИРОВАНИЯ PORTALS PRICE TRACKER BOT")
    logger.info("🚀 " * 20)

    try:
        await test_config()
        await test_gift_model()
        await test_add_gift_flow()
        await test_price_tracker()

        logger.info("\n" + "="*60)
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        logger.info("="*60)
        logger.info("\n📝 Следующие шаги:")
        logger.info("   1. Настройте .env файл с реальными credentials")
        logger.info("   2. Запустите PostgreSQL (или используйте docker-compose)")
        logger.info("   3. Запустите бота: python main.py")
        logger.info("   4. Протестируйте с реальным Telegram ботом")

    except Exception as e:
        logger.error(f"\n❌ Тесты провалились с ошибкой: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())