"""Новый сервис для отслеживания правил и отправки алертов."""

import asyncio
import logging
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta
from aiogram import Bot

from src.config import get_settings
from src.repositories import TrackingRuleRepository, AlertRepository
from src.models import TrackingRule, Alert, ConditionType
from src.services.portals_service import PortalsService
from src.keyboards import get_alert_keyboard

logger = logging.getLogger(__name__)


class TrackingPriceTracker:
    """Сервис для мониторинга правил отслеживания и отправки алертов."""

    def __init__(self, bot: Bot, portals_service: PortalsService = None):
        self.bot = bot
        self.settings = get_settings()
        self.rule_repo = TrackingRuleRepository()
        self.alert_repo = AlertRepository()
        self.api = portals_service or PortalsService()
        self._running = False

        # Rate limiting: не более 3 алертов в минуту для одного пользователя
        self._user_alert_timestamps: Dict[int, List[datetime]] = defaultdict(list)
        self._alerts_per_minute_limit = 3

        # Cooldown: после алерта правило "отдыхает" 60 секунд
        self._rule_cooldowns: Dict[int, datetime] = {}
        self._rule_cooldown_seconds = 60

        # User pause: пауза всех алертов для пользователя (приоритет интерфейса)
        self._user_pauses: Dict[int, datetime] = {}
        self._user_pause_seconds = 15

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

    def _is_rule_on_cooldown(self, rule_id: int) -> bool:
        """Проверяет, находится ли правило на cooldown."""
        if rule_id not in self._rule_cooldowns:
            return False

        cooldown_until = self._rule_cooldowns[rule_id]
        if datetime.now() < cooldown_until:
            return True

        # Cooldown истёк, удаляем
        del self._rule_cooldowns[rule_id]
        return False

    def _set_rule_cooldown(self, rule_id: int) -> None:
        """Устанавливает cooldown для правила."""
        self._rule_cooldowns[rule_id] = datetime.now() + timedelta(seconds=self._rule_cooldown_seconds)

    def _can_send_alert_to_user(self, user_id: int) -> bool:
        """Проверяет, можно ли отправить алерт пользователю (rate limit)."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Очищаем старые timestamps
        self._user_alert_timestamps[user_id] = [
            ts for ts in self._user_alert_timestamps[user_id]
            if ts > one_minute_ago
        ]

        # Проверяем лимит
        return len(self._user_alert_timestamps[user_id]) < self._alerts_per_minute_limit

    def _register_alert_sent(self, user_id: int) -> None:
        """Регистрирует отправленный алерт для rate limiting."""
        self._user_alert_timestamps[user_id].append(datetime.now())

    def _is_user_paused(self, user_id: int) -> bool:
        """Проверяет, на паузе ли пользователь (приоритет интерфейса)."""
        if user_id not in self._user_pauses:
            return False

        pause_until = self._user_pauses[user_id]
        if datetime.now() < pause_until:
            return True

        # Пауза истекла, удаляем
        del self._user_pauses[user_id]
        return False

    def pause_user_alerts(self, user_id: int) -> None:
        """
        Ставит алерты пользователя на паузу (вызывается из хендлеров).

        Используется для приоритета интерфейса над алертами -
        когда пользователь нажимает кнопки меню, алерты временно останавливаются.
        """
        self._user_pauses[user_id] = datetime.now() + timedelta(seconds=self._user_pause_seconds)
        logger.info(f"User {user_id} alerts paused for {self._user_pause_seconds}s (UI priority)")

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
            # ПРИОРИТЕТ ИНТЕРФЕЙСА: проверяем, не на паузе ли пользователь
            if self._is_user_paused(rule.user_id):
                logger.debug(f"User {rule.user_id} is paused (UI priority), skipping rule #{rule.rule_id}")
                return

            # Проверяем cooldown правила
            if self._is_rule_on_cooldown(rule.rule_id):
                logger.debug(f"Rule #{rule.rule_id} is on cooldown, skipping")
                return
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
                floor_price = float(models_floors.get(lot["model"], lot.get("floor_price", 0)) or 0)

                if rule.matches_lot(lot["price"], floor_price):
                    # Проверяем, не отправляли ли уже алерт по этому лоту
                    already_sent = await self.alert_repo.lot_already_alerted(
                        rule.rule_id, lot["id"]
                    )

                    if not already_sent:
                        matching_lots.append(lot)

            # Отправляем алерты для найденных лотов
            alerts_sent = 0
            for lot in matching_lots[:5]:  # Максимум 5 алертов за раз
                # Проверяем rate limit пользователя
                if not self._can_send_alert_to_user(rule.user_id):
                    logger.warning(f"Rate limit reached for user {rule.user_id}, stopping alerts")
                    break

                # Отправляем алерт асинхронно (не блокируем event loop)
                asyncio.create_task(self._send_alert(rule, lot, models_floors))

                # Регистрируем отправленный алерт
                self._register_alert_sent(rule.user_id)
                alerts_sent += 1

                # Небольшая задержка между алертами, чтобы event loop успевал обрабатывать команды
                await asyncio.sleep(0.5)

            # Если отправили хотя бы один алерт, устанавливаем cooldown для правила
            if alerts_sent > 0:
                self._set_rule_cooldown(rule.rule_id)
                logger.info(
                    f"Sent {alerts_sent} alerts for rule #{rule.rule_id}, cooldown set for {self._rule_cooldown_seconds}s"
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
                floor_price = float(models_floors[rule.model])
            else:
                # Берём средний floor если модель не указана
                floor_price = (
                    sum(float(v) for v in models_floors.values()) / len(models_floors)
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
            lot_floor_price = float(models_floors.get(lot["model"], lot.get("floor_price", 0)) or 0)
            # Формат: https://t.me/portals/market?startapp=gift_{id}
            # где id включает UUID и суффикс (например: abc-123_k74zqq)
            lot_url = f"https://t.me/portals/market?startapp=gift_{lot['id']}"

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
