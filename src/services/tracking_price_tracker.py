"""Новый сервис для отслеживания правил и отправки алертов."""

import asyncio
import logging
from typing import List, Dict, Any
from collections import defaultdict
from aiogram import Bot

from src.config import get_settings
from src.repositories import TrackingRuleRepository, AlertRepository
from src.models import TrackingRule, Alert, ConditionType
from src.services.portals_api_mock import get_mock_api
from src.keyboards import get_alert_keyboard

logger = logging.getLogger(__name__)


class TrackingPriceTracker:
    """Сервис для мониторинга правил отслеживания и отправки алертов."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.settings = get_settings()
        self.rule_repo = TrackingRuleRepository()
        self.alert_repo = AlertRepository()
        self.api = get_mock_api()
        self._running = False

    async def check_all_rules(self) -> None:
        """Проверяет все активные правила отслеживания."""
        try:
            rules = await self.rule_repo.get_all_active()
            logger.info(f"Checking {len(rules)} active tracking rules")

            if not rules:
                return

            # Группируем правила по коллекциям для оптимизации запросов
            rules_by_collection = self._group_rules_by_collection(rules)

            for collection_name, collection_rules in rules_by_collection.items():
                await self._check_collection_rules(collection_name, collection_rules)

        except Exception as e:
            logger.error(f"Error in check_all_rules: {e}", exc_info=True)

    def _group_rules_by_collection(
        self, rules: List[TrackingRule]
    ) -> Dict[str, List[TrackingRule]]:
        """
        Группирует правила по коллекциям.

        Args:
            rules: Список правил

        Returns:
            Словарь {collection_name: [rules]}
        """
        grouped = defaultdict(list)
        for rule in rules:
            grouped[rule.collection_name].append(rule)
        return dict(grouped)

    async def _check_collection_rules(
        self, collection_name: str, rules: List[TrackingRule]
    ) -> None:
        """
        Проверяет все правила для одной коллекции.

        Args:
            collection_name: Название коллекции
            rules: Правила для этой коллекции
        """
        try:
            # Получаем floor данные для коллекции
            floors_data = await self.api.filterFloors(gift_name=collection_name)
            models_floors = floors_data.get("models", {})

            for rule in rules:
                await self._check_single_rule(rule, models_floors)

        except Exception as e:
            logger.error(f"Error checking rules for collection '{collection_name}': {e}")

    async def _check_single_rule(
        self, rule: TrackingRule, models_floors: Dict[str, float]
    ) -> None:
        """
        Проверяет одно правило и отправляет алерты при совпадении.

        Args:
            rule: Правило отслеживания
            models_floors: Словарь floor цен по моделям
        """
        try:
            # Вычисляем максимальную цену для поиска
            max_price = self._calculate_max_price(rule, models_floors)

            # Ищем лоты через API
            lots = await self.api.search(
                gift_name=rule.collection_name,
                model=rule.model if rule.model else "",
                max_price=int(max_price) if max_price else 100000,
                sort="price_asc",
                limit=50,
            )

            if not lots:
                logger.debug(f"No lots found for rule #{rule.rule_id}")
                return

            # Фильтруем лоты по условиям правила
            matching_lots = []
            for lot in lots:
                floor_price = models_floors.get(lot["model"], lot.get("floor_price", 0))

                if rule.matches_lot(lot["price"], floor_price):
                    # Проверяем, не отправляли ли уже алерт по этому лоту
                    already_sent = await self.alert_repo.lot_already_alerted(
                        rule.rule_id, lot["id"]
                    )

                    if not already_sent:
                        matching_lots.append(lot)

            # Отправляем алерты для найденных лотов
            for lot in matching_lots[:5]:  # Максимум 5 алертов за раз
                await self._send_alert(rule, lot, models_floors)

            if matching_lots:
                logger.info(
                    f"Sent {len(matching_lots[:5])} alerts for rule #{rule.rule_id}"
                )

        except Exception as e:
            logger.error(f"Error checking rule #{rule.rule_id}: {e}", exc_info=True)

    def _calculate_max_price(
        self, rule: TrackingRule, models_floors: Dict[str, float]
    ) -> float:
        """
        Вычисляет максимальную цену для поиска лотов.

        Args:
            rule: Правило отслеживания
            models_floors: Floor цены моделей

        Returns:
            Максимальная цена для API запроса
        """
        if rule.condition_type == ConditionType.FIXED_PRICE:
            return rule.target_price if rule.target_price else 100000

        if rule.condition_type == ConditionType.FLOOR_DISCOUNT:
            if rule.model and rule.model in models_floors:
                floor_price = models_floors[rule.model]
            else:
                # Берём средний floor если модель не указана
                floor_price = (
                    sum(models_floors.values()) / len(models_floors)
                    if models_floors
                    else 100
                )

            if rule.floor_discount_percent:
                threshold = floor_price * (1 - rule.floor_discount_percent / 100)
                return threshold

        # ANY_PRICE - возвращаем большое число
        return 100000

    async def _send_alert(
        self, rule: TrackingRule, lot: Dict[str, Any], models_floors: Dict[str, float]
    ) -> None:
        """
        Создаёт и отправляет алерт пользователю.

        Args:
            rule: Правило отслеживания
            lot: Данные о лоте
            models_floors: Floor цены моделей
        """
        try:
            # Создаём объект Alert
            lot_floor_price = models_floors.get(lot["model"], lot.get("floor_price", 0))
            lot_url = f"https://t.me/portals?startapp=gift-{lot['id']}"

            alert = Alert(
                rule_id=rule.rule_id,
                user_id=rule.user_id,
                lot_id=lot["id"],
                lot_price=lot["price"],
                lot_floor_price=lot_floor_price,
                collection_name=lot["name"],
                model=lot["model"],
                photo_url=lot.get("photo_url"),
                lot_url=lot_url,
            )

            # Сохраняем в БД
            alert_id = await self.alert_repo.create(alert)
            alert.alert_id = alert_id

            # Формируем сообщение
            message_text = alert.format_message()
            keyboard = get_alert_keyboard(lot_url, rule.rule_id)

            # Отправляем пользователю
            if lot.get("photo_url"):
                try:
                    await self.bot.send_photo(
                        chat_id=rule.user_id,
                        photo=lot["photo_url"],
                        caption=message_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.error(f"Error sending photo: {e}")
                    await self.bot.send_message(
                        chat_id=rule.user_id,
                        text=message_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown",
                    )
            else:
                await self.bot.send_message(
                    chat_id=rule.user_id,
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )

            # Отмечаем как отправленный
            await self.alert_repo.mark_as_sent(alert_id)

            logger.info(f"Alert sent: rule #{rule.rule_id}, lot {lot['id']}, user {rule.user_id}")

        except Exception as e:
            logger.error(f"Error sending alert: {e}", exc_info=True)

    async def start(self) -> None:
        """Запускает мониторинг правил."""
        if self._running:
            logger.warning("Tracking price tracker is already running")
            return

        self._running = True
        logger.info("Tracking price tracker started")

        # Инициализация API если нужно
        # await self.api.init_auth()  # Для реального API

        while self._running:
            try:
                await self.check_all_rules()
            except Exception as e:
                logger.error(f"Error in tracker loop: {e}", exc_info=True)

            await asyncio.sleep(self.settings.price_check_interval)

    def stop(self) -> None:
        """Останавливает мониторинг."""
        self._running = False
        logger.info("Tracking price tracker stopped")
