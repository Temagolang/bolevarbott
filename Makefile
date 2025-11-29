.PHONY: help install run stop restart logs clean test deploy

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

db-up: ## Запустить только базу данных (Docker)
	@echo "$(GREEN)Запуск PostgreSQL...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ База данных запущена$(NC)"
	@sleep 3
	@echo "$(YELLOW)Ожидание готовности БД...$(NC)"

db-stop: ## Остановить базу данных
	@echo "$(YELLOW)Остановка PostgreSQL...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ База данных остановлена$(NC)"

db-logs: ## Показать логи базы данных
	docker-compose logs -f postgres

run: ## Запустить весь проект (БД + бот) в Docker
	@echo "$(GREEN)Запуск проекта в Docker...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Проект запущен в Docker$(NC)"
	@echo "$(YELLOW)Смотри логи: make logs$(NC)"

run-dev: db-up ## Запустить в режиме разработки с автоперезагрузкой
	@echo "$(GREEN)Запуск бота в режиме разработки...$(NC)"
	@echo "$(YELLOW)Для остановки нажмите Ctrl+C$(NC)"
	python main.py

stop: ## Остановить все (БД + бот)
	@echo "$(YELLOW)Остановка проекта...$(NC)"
	docker-compose down
	@pkill -f "python main.py" || true
	@echo "$(GREEN)✓ Проект остановлен$(NC)"

restart: stop run ## Перезапустить проект

logs: ## Показать логи Docker контейнеров
	docker-compose logs -f

clean: ## Очистить временные файлы и остановить контейнеры
	@echo "$(YELLOW)Очистка...$(NC)"
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Очистка завершена$(NC)"

test: ## Запустить тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	pytest tests/ -v

format: ## Форматировать код (black)
	@echo "$(GREEN)Форматирование кода...$(NC)"
	black src/ main.py
	@echo "$(GREEN)✓ Код отформатирован$(NC)"

# === Команды для деплоя на удаленный сервер ===

REMOTE_USER ?= root
REMOTE_HOST ?= your-server.com
REMOTE_PATH ?= /opt/bolevarbott

deploy-setup: ## Первоначальная настройка на удаленном сервере
	@echo "$(GREEN)Настройка удаленного сервера...$(NC)"
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "mkdir -p $(REMOTE_PATH)"
	@echo "$(GREEN)✓ Директория создана$(NC)"

deploy-copy: ## Копировать файлы на сервер
	@echo "$(GREEN)Копирование файлов на сервер...$(NC)"
	rsync -avz --exclude='.git' \
		--exclude='__pycache__' \
		--exclude='*.pyc' \
		--exclude='.env' \
		--exclude='.idea' \
		--exclude='.DS_Store' \
		. $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_PATH)/
	@echo "$(GREEN)✓ Файлы скопированы$(NC)"
	@echo "$(YELLOW)⚠ Не забудь скопировать .env файл отдельно!$(NC)"

deploy-env: ## Копировать .env на сервер (ОСТОРОЖНО!)
	@echo "$(YELLOW)Копирование .env файла...$(NC)"
	scp .env $(REMOTE_USER)@$(REMOTE_HOST):$(REMOTE_PATH)/.env
	@echo "$(GREEN)✓ .env скопирован$(NC)"

deploy-install: ## Установить зависимости на сервере
	@echo "$(GREEN)Установка зависимостей на сервере...$(NC)"
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_PATH) && pip install -r requirements.txt"
	@echo "$(GREEN)✓ Зависимости установлены$(NC)"

deploy-start: ## Запустить бота на сервере
	@echo "$(GREEN)Запуск бота на сервере...$(NC)"
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_PATH) && docker-compose up -d && nohup python main.py > bot.log 2>&1 &"
	@echo "$(GREEN)✓ Бот запущен на сервере$(NC)"

deploy-stop: ## Остановить бота на сервере
	@echo "$(YELLOW)Остановка бота на сервере...$(NC)"
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "cd $(REMOTE_PATH) && docker-compose down && pkill -f 'python main.py' || true"
	@echo "$(GREEN)✓ Бот остановлен$(NC)"

deploy-logs: ## Показать логи бота на сервере
	ssh $(REMOTE_USER)@$(REMOTE_HOST) "tail -f $(REMOTE_PATH)/bot.log"

deploy-full: deploy-copy deploy-install deploy-start ## Полный деплой (копирование + установка + запуск)
	@echo "$(GREEN)✓ Деплой завершен!$(NC)"
	@echo "$(YELLOW)Проверь логи: make deploy-logs$(NC)"

# === Docker команды ===

docker-build: ## Собрать Docker образ бота
	@echo "$(GREEN)Сборка Docker образа...$(NC)"
	docker build -t bolevarbott .
	@echo "$(GREEN)✓ Образ собран$(NC)"

docker-run: ## Запустить бота в Docker
	@echo "$(GREEN)Запуск бота в Docker...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Бот запущен в Docker$(NC)"

docker-rebuild: ## Пересобрать и перезапустить Docker контейнеры
	@echo "$(GREEN)Пересборка контейнеров...$(NC)"
	docker-compose up -d --build
	@echo "$(GREEN)✓ Контейнеры пересобраны$(NC)"

# === Информация ===

status: ## Показать статус сервисов
	@echo "$(GREEN)=== Статус локальных сервисов ====$(NC)"
	@docker-compose ps 2>/dev/null || echo "$(RED)Docker не запущен$(NC)"
	@echo ""
	@echo "$(GREEN)=== Процессы бота ====$(NC)"
	@ps aux | grep "python main.py" | grep -v grep || echo "$(YELLOW)Бот не запущен$(NC)"

check-env: ## Проверить наличие .env файла
	@if [ -f .env ]; then \
		echo "$(GREEN)✓ .env файл найден$(NC)"; \
	else \
		echo "$(RED)✗ .env файл не найден!$(NC)"; \
		echo "$(YELLOW)Создай .env на основе .env.example$(NC)"; \
		exit 1; \
	fi