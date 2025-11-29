# Portals Price Tracker Bot

Telegram бот для отслеживания цен на подарки в Portals маркете. Автоматически мониторит изменения цен и уведомляет пользователей о снижении стоимости отслеживаемых подарков.

## Версия 2.0 - Tracking Rules

### Новый функционал

- **Правила отслеживания** - Создавайте гибкие правила с условиями
- **Inline меню** - Удобная навигация через кнопки без спама сообщениями
- **3 типа условий**:
  - Фиксированная цена (≤ X TON)
  - Скидка от floor (ниже пола на X%)
  - Любая цена (уведомления о всех новых лотах)
- **Управление правилами** - Просмотр, пауза/возобновление, удаление
- **Умные алерты** - Без дубликатов, с группировкой запросов к API

### Legacy функционал (V1.0)

- **Добавление подарков** - Пользователи могут добавлять подарки для отслеживания через простой диалог
- **Автоматический мониторинг** - Бот проверяет цены каждые 60 секунд (настраивается)
- **Уведомления о снижении цен** - Мгновенные уведомления при падении цены или floor price
- **Интеграция с Portals** - Прямые ссылки на подарки в Portals маркете
- **Фотографии подарков** - Визуальное отображение отслеживаемых товаров

## Технологический стек

- **Python 3.11+**
- **aiogram 3.x** - Telegram Bot Framework
- **PostgreSQL** - База данных
- **asyncpg** - Асинхронный драйвер для PostgreSQL
- **aportalsmp** - Асинхронная библиотека для работы с Portals API
- **Docker & Docker Compose** - Контейнеризация и деплой

## Архитектура

Проект построен с использованием чистой архитектуры и разделением ответственности:

```
src/
├── config/          # Конфигурация и настройки
├── database/        # Подключение к БД и схемы
├── models/          # Модели данных (Gift, TrackingRule, Alert)
├── repositories/    # Слой работы с БД
├── services/        # Бизнес-логика (Price Trackers, Portals API)
├── handlers/        # Telegram обработчики
│   ├── menu.py         # Главное меню и навигация
│   ├── add_tracking.py # Мастер создания правил (V2)
│   └── add_gift.py     # Legacy функционал (V1)
├── keyboards.py     # Inline клавиатуры
└── bot.py          # Инициализация бота
```

Подробнее см. [ARCHITECTURE.md](./ARCHITECTURE.md)

## Быстрый старт

### Требования

- Python 3.11+
- PostgreSQL 15+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- Portals API credentials (API_ID и API_HASH)

### Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd bolevarbott
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив ваши credentials
```

5. Запустите бота:
```bash
python main.py
```

## Использование с Docker

### Запуск через Docker Compose

1. Настройте `.env` файл с вашими credentials

2. Запустите сервисы:
```bash
docker-compose up -d
```

3. Проверьте логи:
```bash
docker-compose logs -f bot
```

4. Остановка:
```bash
docker-compose down
```

### Пересборка после изменений

```bash
docker-compose up -d --build
```

## Конфигурация

Все настройки задаются через переменные окружения в файле `.env`:

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|---------------------|
| `BOT_TOKEN` | Токен Telegram бота | - |
| `API_ID` | Telegram API ID для Portals | - |
| `API_HASH` | Telegram API Hash для Portals | - |
| `DB_HOST` | Хост PostgreSQL | `localhost` |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `DB_USER` | Пользователь БД | `postgres` |
| `DB_PASSWORD` | Пароль БД | - |
| `DB_NAME` | Имя базы данных | `portals_bot` |
| `PRICE_CHECK_INTERVAL` | Интервал проверки цен (сек) | `60` |

## Использование бота

### Команды

- `/start` - Главное меню с inline-кнопками
- `/my` - Список ваших правил отслеживания
- `/add` - Legacy функционал (добавление подарка напрямую)

### Создание правила отслеживания (V2)

1. Нажмите "➕ Добавить отслеживание" в `/start`
2. Выберите тип поиска (по коллекции / по имени)
3. Введите название коллекции (например: "Toy Bear")
4. Выберите модель из списка или пропустите
5. Настройте ценовое условие:
   - **Фиксированная цена**: уведомления когда цена ≤ X TON
   - **Скидка от floor**: когда цена ≤ floor - X%
6. Подтвердите создание правила

### Управление правилами

В `/my`:
- Просмотр всех правил с текущим статусом
- Клик на правило → детали + история срабатываний
- Пауза/возобновление отслеживания
- Удаление правила

### Процесс добавления подарка (Legacy V1)

1. Отправьте команду `/add`
2. Введите название подарка (name)
3. Введите модель подарка (model)
4. Бот найдет подарок в Portals и добавит его в мониторинг
5. Вы получите карточку с текущей ценой и ссылкой на Portals

### Уведомления

Бот автоматически отправляет уведомления когда:
- Цена подарка снижается
- Floor price снижается

Уведомление содержит:
- Название и модель подарка
- Старую и новую цену
- Старый и новый floor price
- Фото подарка
- Прямую ссылку на Portals маркет

## Разработка

### Структура базы данных

**V2.0 таблицы:**

```sql
-- Правила отслеживания
CREATE TABLE tracking_rules (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    model VARCHAR(255),
    condition_type VARCHAR(50) NOT NULL,
    target_price DECIMAL(10, 2),
    floor_discount_percent INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- История алертов
CREATE TABLE alerts (
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
```

**V1.0 таблица (legacy):**

```sql
CREATE TABLE gifts (
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
```

### Тестирование

```bash
# Установка dev зависимостей
pip install -r requirements-dev.txt

# Запуск тестов
pytest

# С покрытием
pytest --cov=src
```

## Troubleshooting

### Проблемы с подключением к БД

Убедитесь что:
- PostgreSQL запущен и доступен
- Credentials в `.env` корректны
- База данных создана

### Ошибки аутентификации Portals API

- Проверьте правильность `API_ID` и `API_HASH`
- Убедитесь что aportalsmp установлен корректно

### Бот не отправляет уведомления

- Проверьте что price tracker запущен (см. логи)
- Убедитесь что `PRICE_CHECK_INTERVAL` не слишком большой
- Проверьте наличие подарков в БД

## Roadmap

**V2.0 (в процессе):**
- [x] Правила отслеживания с условиями
- [x] Inline меню и навигация
- [x] Управление правилами (пауза/удаление)
- [ ] Реальная интеграция с Portals API (сейчас моки)
- [ ] Фильтры по редкости, символам, фонам
- [ ] Статистика по правилам

**V3.0 (планируется):**
- [ ] Автопокупка лотов при совпадении условий
- [ ] Интеграция с кошельком
- [ ] Лимиты на покупки
- [ ] История транзакций

**Другое:**
- [ ] Web dashboard для управления
- [ ] Экспорт истории алертов
- [ ] Rate limiting и throttling для API
- [ ] Telegram Mini App интерфейс

## Лицензия

MIT

## Поддержка

При возникновении проблем создавайте Issue в репозитории.