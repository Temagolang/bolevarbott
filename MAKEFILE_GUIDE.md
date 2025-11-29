# Makefile Guide - Руководство по командам

## Быстрый старт

### Локальный запуск
```bash
# Показать все команды
make help

# Установить зависимости
make install

# Запустить проект (БД + бот)
make run

# Остановить все
make stop

# Перезапустить
make restart

# Посмотреть логи
make logs
```

## Основные команды

### Разработка

| Команда | Описание |
|---------|----------|
| `make help` | Показать все доступные команды |
| `make install` | Установить Python зависимости |
| `make run` | Запустить БД + бота |
| `make run-dev` | Запустить в режиме разработки |
| `make stop` | Остановить все сервисы |
| `make restart` | Перезапустить проект |
| `make status` | Показать статус сервисов |

### База данных

| Команда | Описание |
|---------|----------|
| `make db-up` | Запустить только PostgreSQL |
| `make db-stop` | Остановить PostgreSQL |
| `make db-logs` | Логи базы данных |

### Тестирование и качество кода

| Команда | Описание |
|---------|----------|
| `make test` | Запустить тесты |
| `make format` | Отформатировать код (black) |
| `make clean` | Очистить временные файлы |

### Docker

| Команда | Описание |
|---------|----------|
| `make docker-build` | Собрать Docker образ |
| `make docker-run` | Запустить в Docker |
| `make docker-rebuild` | Пересобрать и перезапустить |

## Деплой на удаленный сервер

### Первоначальная настройка

```bash
# 1. Настроить переменные (в Makefile или через export)
export REMOTE_USER=root
export REMOTE_HOST=123.456.789.0
export REMOTE_PATH=/opt/bolevarbott

# 2. Создать директорию на сервере
make deploy-setup

# 3. Полный деплой
make deploy-full
```

### Управление на сервере

| Команда | Описание |
|---------|----------|
| `make deploy-copy` | Скопировать файлы на сервер |
| `make deploy-env` | Скопировать .env на сервер |
| `make deploy-install` | Установить зависимости |
| `make deploy-start` | Запустить бота на сервере |
| `make deploy-stop` | Остановить бота на сервере |
| `make deploy-logs` | Показать логи на сервере |
| `make deploy-full` | Полный деплой (все в одной команде) |

### Пример полного деплоя

```bash
# 1. Настроить .env локально
cp .env.example .env
# Отредактировать .env

# 2. Указать сервер
export REMOTE_HOST=123.456.789.0
export REMOTE_USER=root

# 3. Деплой
make deploy-setup      # Первый раз
make deploy-copy       # Копируем код
make deploy-env        # Копируем .env
make deploy-install    # Устанавливаем зависимости
make deploy-start      # Запускаем

# Или все одной командой (после deploy-setup)
make deploy-full

# 4. Проверить логи
make deploy-logs
```

## Настройка переменных окружения

### Вариант 1: В командной строке
```bash
make deploy-copy REMOTE_HOST=123.456.789.0 REMOTE_USER=admin
```

### Вариант 2: Через export
```bash
export REMOTE_HOST=123.456.789.0
export REMOTE_USER=admin
export REMOTE_PATH=/home/admin/bot
make deploy-full
```

### Вариант 3: В .bashrc/.zshrc (постоянно)
```bash
echo 'export REMOTE_HOST=123.456.789.0' >> ~/.zshrc
echo 'export REMOTE_USER=admin' >> ~/.zshrc
source ~/.zshrc
```

## Типичные сценарии

### Локальная разработка
```bash
# Первый запуск
make install
make run

# Работа
# ... вносим изменения ...
make restart

# Тестирование
make test
make format
```

### Деплой обновлений на сервер
```bash
# Быстрый деплой изменений
make deploy-copy
make deploy-stop
make deploy-start

# Или полный (с установкой зависимостей)
make deploy-full
```

### Отладка на сервере
```bash
# Смотрим логи
make deploy-logs

# Останавливаем
make deploy-stop

# Вносим изменения локально
# ...

# Деплоим и запускаем
make deploy-copy
make deploy-start
```

## Полезные советы

1. **SSH ключи**: Настрой SSH ключи для автоматического входа:
   ```bash
   ssh-copy-id root@your-server.com
   ```

2. **Проверка статуса**: Перед деплоем проверь текущий статус:
   ```bash
   make status
   ```

3. **Логи**: Всегда проверяй логи после деплоя:
   ```bash
   make deploy-logs
   ```

4. **Безопасность .env**: Будь осторожен с `make deploy-env` - передаешь секреты!

5. **Автоматизация**: Добавь в crontab для автоперезапуска:
   ```bash
   0 */6 * * * cd /opt/bolevarbott && docker-compose restart
   ```

## Устранение проблем

### Docker не запущен
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

### Ошибка подключения к серверу
```bash
# Проверь SSH
ssh root@your-server.com

# Проверь переменные
echo $REMOTE_HOST
echo $REMOTE_USER
```

### Бот не запускается
```bash
# Проверь .env
make check-env

# Проверь логи
make logs
make deploy-logs  # на сервере
```

### База не поднимается
```bash
# Остановить и очистить
make clean

# Запустить заново
make db-up
```