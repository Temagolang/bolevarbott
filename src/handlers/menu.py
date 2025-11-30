"""Хэндлеры для главного меню и навигации."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.keyboards import (
    get_main_menu_keyboard,
    get_back_to_main_keyboard,
    get_rule_actions_keyboard,
    get_delete_confirmation_keyboard,
)
from src.repositories import TrackingRuleRepository, AlertRepository
from src.services.user_cache import get_user_cache

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start - главное меню."""
    text = (
        "Привет! Я бот для отслеживания лотов на Portals Marketplace.\n\n"
        "Я могу:\n"
        "• следить за коллекциями и моделями по заданной цене\n"
        "• присылать тебе ссылки на интересные лоты\n\n"
        "Что делаем?"
    )

    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery):
    """Возврат в главное меню."""
    # ПРИОРИТЕТ ИНТЕРФЕЙСА: ставим алерты на паузу, когда пользователь работает с меню
    bot = callback.bot
    if hasattr(bot, 'tracking_tracker'):
        bot.tracking_tracker.pause_user_alerts(callback.from_user.id)

    text = (
        "Привет! Я бот для отслеживания лотов на Portals Marketplace.\n\n"
        "Я могу:\n"
        "• следить за коллекциями и моделями по заданной цене\n"
        "• присылать тебе ссылки на интересные лоты\n\n"
        "Что делаем?"
    )

    # Всегда отправляем новое сообщение - так меню не перекроется алертами
    await bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.message(Command("my"))
async def cmd_my_trackings(message: Message):
    """Команда /my - список правил пользователя и его группы."""
    await show_my_trackings(message.from_user.id, message.from_user.username, message)


@router.callback_query(F.data == "menu:my_trackings")
async def menu_my_trackings(callback: CallbackQuery):
    """Callback для показа списка правил."""
    # ПРИОРИТЕТ ИНТЕРФЕЙСА: ставим алерты на паузу
    bot = callback.bot
    if hasattr(bot, 'tracking_tracker'):
        bot.tracking_tracker.pause_user_alerts(callback.from_user.id)

    await show_my_trackings(callback.from_user.id, callback.from_user.username, callback.message, callback)


async def show_my_trackings(user_id: int, username: str, message: Message, callback: CallbackQuery = None):
    """
    Показывает список правил отслеживания пользователя и его группы.

    Args:
        user_id: ID пользователя
        username: Username пользователя
        message: Объект сообщения
        callback: Объект callback (если вызов через inline кнопку)
    """
    rule_repo = TrackingRuleRepository()
    user_cache = get_user_cache()

    try:
        # Получаем user_id всех членов группы
        group_user_ids = user_cache.get_group_user_ids(username) if username else [user_id]

        # Если кэш пуст - используем текущего пользователя
        if not group_user_ids:
            group_user_ids = [user_id]
        elif user_id not in group_user_ids:
            # Убедимся что текущий пользователь в списке
            group_user_ids.append(user_id)

        # Получаем правила всей группы
        rules = await rule_repo.get_by_user_ids(group_user_ids)

        if not rules:
            text = (
                "📋 У тебя пока нет правил отслеживания.\n\n"
                "Нажми '➕ Добавить отслеживание', чтобы создать первое правило!"
            )
            keyboard = get_back_to_main_keyboard()
        else:
            # Если в группе несколько человек, показываем это
            is_group = len(group_user_ids) > 1
            if is_group:
                text = "📋 Правила отслеживания вашей команды:\n\n"
            else:
                text = "📋 Твои правила отслеживания:\n\n"

            # Формируем список правил с эмодзи
            for idx, rule in enumerate(rules, 1):
                status_emoji = "✅" if rule.is_active else "⏸"
                model_text = rule.model if rule.model else "любая модель"

                text += f"{idx}️⃣ **{rule.collection_name} / {model_text}**\n"

                # Условие
                if rule.condition_type.value == "fixed_price":
                    text += f"   • цена ≤ {rule.target_price} TON\n"
                elif rule.condition_type.value == "floor_discount":
                    text += f"   • ниже floor на {rule.floor_discount_percent}%\n"
                elif rule.condition_type.value == "any_price":
                    text += f"   • любая цена\n"

                text += f"   • статус: {status_emoji} {'активно' if rule.is_active else 'на паузе'}\n\n"

            text += "\nВыбери правило, чтобы посмотреть детали или изменить."

            # Создаём inline кнопки для каждого правила
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

            buttons = []
            for idx, rule in enumerate(rules, 1):
                model_text = rule.model if rule.model else "любая"
                button_text = f"{idx}️⃣ {rule.collection_name[:15]}... / {model_text[:10]}..."
                buttons.append(
                    [InlineKeyboardButton(text=button_text, callback_data=f"rule:view:{rule.rule_id}")]
                )

            buttons.append(
                [InlineKeyboardButton(text="➕ Добавить", callback_data="menu:add_tracking")]
            )
            buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Редактируем или отправляем новое сообщение
        if callback:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
            await callback.answer()
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error showing trackings: {e}", exc_info=True)
        error_text = "❌ Ошибка при загрузке правил отслеживания"

        if callback:
            await callback.message.edit_text(error_text, reply_markup=get_back_to_main_keyboard())
            await callback.answer()
        else:
            await message.answer(error_text, reply_markup=get_back_to_main_keyboard())


@router.callback_query(F.data.startswith("rule:view:"))
async def rule_view(callback: CallbackQuery):
    """Показ деталей правила."""
    # ПРИОРИТЕТ ИНТЕРФЕЙСА: ставим алерты на паузу
    bot = callback.bot
    if hasattr(bot, 'tracking_tracker'):
        bot.tracking_tracker.pause_user_alerts(callback.from_user.id)

    rule_id = int(callback.data.split(":")[2])

    rule_repo = TrackingRuleRepository()
    alert_repo = AlertRepository()

    try:
        rule = await rule_repo.get_by_id(rule_id)

        if not rule:
            await callback.answer("Правило не найдено", show_alert=True)
            return

        # Получаем последние срабатывания
        recent_alerts = await alert_repo.get_by_rule(rule_id, limit=5)

        model_text = rule.model if rule.model else "любая модель"
        text = f"📌 Правило #{rule.rule_id}\n\n"
        text += f"Коллекция: **{rule.collection_name}**\n"
        text += f"Модель: **{model_text}**\n\n"
        text += "Условие:\n"

        if rule.condition_type.value == "fixed_price":
            text += f"• цена ≤ {rule.target_price} TON\n"
        elif rule.condition_type.value == "floor_discount":
            text += f"• ниже floor на {rule.floor_discount_percent}%\n"
        elif rule.condition_type.value == "any_price":
            text += f"• любая цена\n"

        status_text = "✅ активно" if rule.is_active else "⏸ на паузе"
        text += f"\nСтатус: {status_text}\n"

        # Последние срабатывания
        if recent_alerts:
            text += "\n📊 Последние срабатывания:\n"
            for alert in recent_alerts:
                date_str = alert.created_at.strftime("%d.%m %H:%M") if alert.created_at else "N/A"
                text += f"• {date_str} — {alert.lot_price} TON\n"
        else:
            text += "\n📊 Срабатываний пока не было\n"

        keyboard = get_rule_actions_keyboard(rule_id, rule.is_active)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.error(f"Error viewing rule {rule_id}: {e}", exc_info=True)
        await callback.answer("Ошибка при загрузке правила", show_alert=True)


@router.callback_query(F.data.startswith("rule:toggle:"))
async def rule_toggle(callback: CallbackQuery):
    """Переключение активности правила."""
    rule_id = int(callback.data.split(":")[2])

    rule_repo = TrackingRuleRepository()

    try:
        new_status = await rule_repo.toggle_active(rule_id)
        status_text = "включено" if new_status else "поставлено на паузу"

        # Обновляем экран с деталями правила
        await rule_view(callback)
        await callback.answer(f"✅ Правило {status_text}", show_alert=False)

    except Exception as e:
        logger.error(f"Error toggling rule {rule_id}: {e}", exc_info=True)
        await callback.answer("Ошибка при изменении статуса", show_alert=True)


@router.callback_query(F.data.startswith("rule:delete_confirm:"))
async def rule_delete_confirm(callback: CallbackQuery):
    """Подтверждение удаления правила."""
    rule_id = int(callback.data.split(":")[2])

    text = "⚠️ Точно удалить это правило?\n\nВсе данные о срабатываниях будут потеряны."
    keyboard = get_delete_confirmation_keyboard(rule_id)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("rule:delete:"))
async def rule_delete(callback: CallbackQuery):
    """Удаление правила."""
    rule_id = int(callback.data.split(":")[2])

    rule_repo = TrackingRuleRepository()

    try:
        await rule_repo.delete(rule_id)

        text = "✅ Правило удалено"
        await callback.message.edit_text(text, reply_markup=get_back_to_main_keyboard())
        await callback.answer("Правило удалено", show_alert=False)

    except Exception as e:
        logger.error(f"Error deleting rule {rule_id}: {e}", exc_info=True)
        await callback.answer("Ошибка при удалении правила", show_alert=True)


def register_menu_handlers(dp):
    """Регистрирует хэндлеры меню."""
    dp.include_router(router)