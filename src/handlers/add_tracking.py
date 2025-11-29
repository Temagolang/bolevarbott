"""Хэндлеры для добавления правил отслеживания."""

import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.keyboards import (
    get_search_type_keyboard,
    get_model_selection_keyboard,
    get_condition_type_keyboard,
    get_rule_confirmation_keyboard,
    get_rule_created_keyboard,
    get_main_menu_keyboard,
)
from src.models import TrackingRule, ConditionType
from src.repositories import TrackingRuleRepository
from src.services.portals_api_mock import get_mock_api

logger = logging.getLogger(__name__)

router = Router()


class AddTracking(StatesGroup):
    """Состояния FSM для добавления правила отслеживания."""

    waiting_collection_query = State()
    waiting_model_selection = State()
    waiting_target_price = State()
    waiting_floor_discount = State()


@router.callback_query(F.data == "menu:add_tracking")
async def add_tracking_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания правила отслеживания."""
    await state.clear()

    text = (
        "➕ Новое отслеживание\n\n"
        "1️⃣ Выбери, как будем искать:"
    )

    await callback.message.edit_text(text, reply_markup=get_search_type_keyboard())
    await callback.answer()


@router.callback_query(F.data == "search:by_collection")
async def search_by_collection(callback: CallbackQuery, state: FSMContext):
    """Поиск по коллекции."""
    text = (
        "📚 Поиск по коллекции\n\n"
        "Введи название коллекции (например: `Toy Bear`, `Pumpkin Cat`):"
    )

    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AddTracking.waiting_collection_query)
    await callback.answer()


@router.callback_query(F.data == "search:by_name")
async def search_by_name(callback: CallbackQuery, state: FSMContext):
    """Поиск по имени подарка (аналогично поиску по коллекции)."""
    text = (
        "🔍 Поиск по имени подарка\n\n"
        "Введи название подарка (или часть имени):"
    )

    await callback.message.edit_text(text)
    await state.set_state(AddTracking.waiting_collection_query)
    await callback.answer()


@router.message(AddTracking.waiting_collection_query)
async def process_collection_query(message: Message, state: FSMContext):
    """Обработка запроса коллекции."""
    query = message.text.strip()

    # Получаем доступные коллекции через mock API
    api = get_mock_api()

    try:
        collections = await api.collections(limit=100)

        # Фильтруем по запросу пользователя
        matching = [
            c for c in collections
            if query.lower() in c["name"].lower()
        ]

        if not matching:
            await message.answer(
                f"❌ Коллекции с названием '{query}' не найдены.\n\n"
                "Попробуй другое название или используй /start чтобы начать заново."
            )
            await state.clear()
            return

        # Сохраняем найденные коллекции в state
        await state.update_data(
            found_collections=matching,
            search_query=query
        )

        # Показываем найденные коллекции
        text = "Найдены коллекции:\n\n"
        buttons = []

        for idx, coll in enumerate(matching[:10], 1):  # Максимум 10
            text += f"{idx}️⃣ {coll['name']}\n"
            text += f"   Floor: {coll['floor_price']} TON (мин. цена)\n"
            text += f"   Объём 24ч: {coll['volume_24h']} TON\n\n"

            buttons.append([
                InlineKeyboardButton(
                    text=f"{idx}️⃣ {coll['name']}",
                    callback_data=f"select_coll:{idx-1}"
                )
            ])

        text += "Выбери одну:"
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:add_tracking")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error searching collections: {e}", exc_info=True)
        await message.answer(
            "❌ Ошибка при поиске коллекций. Попробуй позже.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(F.data.startswith("select_coll:"))
async def select_collection(callback: CallbackQuery, state: FSMContext):
    """Выбор коллекции из списка."""
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    collections = data.get("found_collections", [])

    if idx >= len(collections):
        await callback.answer("Коллекция не найдена", show_alert=True)
        return

    selected_coll = collections[idx]
    await state.update_data(collection_name=selected_coll["name"])

    # Переходим к выбору модели
    text = (
        f"Коллекция: **{selected_coll['name']}**\n\n"
        f"Добавить фильтр по модели?\n\n"
        f"Например: `Wizard`, `Knight`, `Witch`…"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_model_selection_keyboard("menu:add_tracking"),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "add:select_model")
async def select_model_from_list(callback: CallbackQuery, state: FSMContext):
    """Показ списка моделей для выбора."""
    data = await state.get_data()
    collection_name = data.get("collection_name")

    if not collection_name:
        await callback.answer("Коллекция не выбрана", show_alert=True)
        return

    # Получаем модели через API
    api = get_mock_api()

    try:
        floors_data = await api.filterFloors(gift_name=collection_name)
        models = floors_data.get("models", {})

        if not models:
            await callback.answer("Модели не найдены для этой коллекции", show_alert=True)
            return

        text = f"Модели в коллекции {collection_name}:\n\n"
        buttons = []

        for idx, (model_name, floor_price) in enumerate(models.items(), 1):
            text += f"{idx}️⃣ {model_name} (floor: {floor_price} TON)\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{idx}️⃣ {model_name}",
                    callback_data=f"select_model:{model_name}"
                )
            ])

        text += "\nВыбери модель или нажми 'Пропустить':"
        buttons.append([InlineKeyboardButton(text="Пропустить", callback_data="add:skip_model")])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:add_tracking")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error fetching models: {e}", exc_info=True)
        await callback.answer("Ошибка при загрузке моделей", show_alert=True)


@router.callback_query(F.data.startswith("select_model:"))
async def process_model_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора модели."""
    model_name = callback.data.split(":", 1)[1]
    await state.update_data(model=model_name)

    # Переход к настройке условия
    await show_condition_type_selection(callback, state)


@router.callback_query(F.data == "add:skip_model")
async def skip_model(callback: CallbackQuery, state: FSMContext):
    """Пропуск выбора модели."""
    await state.update_data(model=None)

    # Переход к настройке условия
    await show_condition_type_selection(callback, state)


async def show_condition_type_selection(callback: CallbackQuery, state: FSMContext):
    """Показывает выбор типа ценового условия."""
    text = (
        "Как будем задавать условие по цене?\n\n"
        "1️⃣ Фиксированная цена (≤ X TON)\n"
        "2️⃣ Скидка к floor (ниже пола на X%)"
    )

    await callback.message.edit_text(text, reply_markup=get_condition_type_keyboard())
    await callback.answer()


@router.callback_query(F.data == "condition:fixed_price")
async def condition_fixed_price(callback: CallbackQuery, state: FSMContext):
    """Настройка фиксированной цены."""
    await state.update_data(condition_type=ConditionType.FIXED_PRICE)

    text = (
        "💰 Фиксированная цена\n\n"
        "Введи максимальную цену в TON, по которой тебе интересны лоты.\n\n"
        "Например: `40`"
    )

    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AddTracking.waiting_target_price)
    await callback.answer()


@router.callback_query(F.data == "condition:floor_discount")
async def condition_floor_discount(callback: CallbackQuery, state: FSMContext):
    """Настройка скидки от floor."""
    await state.update_data(condition_type=ConditionType.FLOOR_DISCOUNT)

    # Получаем данные для показа текущего floor
    data = await state.get_data()
    collection_name = data.get("collection_name")
    model = data.get("model")

    # Получаем floor через API
    api = get_mock_api()
    try:
        floors_data = await api.filterFloors(gift_name=collection_name)
        models = floors_data.get("models", {})

        if model and model in models:
            floor_price = models[model]
            floor_info = f"\n💎 Текущий floor для {model}: **{floor_price} TON**\n"
            example_calc = f"Пример: при 10% → цена ≤ {floor_price * 0.9:.1f} TON"
        elif models:
            # Средний floor если модель не выбрана
            avg_floor = sum(models.values()) / len(models)
            floor_info = f"\n💎 Средний floor коллекции: **{avg_floor:.1f} TON**\n"
            example_calc = f"Пример: при 10% → цена ≤ {avg_floor * 0.9:.1f} TON"
        else:
            floor_info = ""
            example_calc = "Пример: при 10% → цена будет на 10% ниже floor"
    except Exception as e:
        logger.error(f"Error getting floor: {e}")
        floor_info = ""
        example_calc = "Пример: при 10% → цена будет на 10% ниже floor"

    text = (
        "📉 Скидка от floor\n"
        f"{floor_info}\n"
        "Введи процент, на который цена должна быть ниже floor.\n\n"
        f"{example_calc}"
    )

    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(AddTracking.waiting_floor_discount)
    await callback.answer()


@router.message(AddTracking.waiting_target_price)
async def process_target_price(message: Message, state: FSMContext):
    """Обработка ввода фиксированной цены."""
    try:
        price = float(message.text.strip())

        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0. Попробуй ещё раз:")
            return

        await state.update_data(target_price=price)

        # Переход к подтверждению
        await show_rule_confirmation(message, state)

    except ValueError:
        await message.answer("❌ Некорректная цена. Введи число, например: 40")


@router.message(AddTracking.waiting_floor_discount)
async def process_floor_discount(message: Message, state: FSMContext):
    """Обработка ввода процента скидки от floor."""
    try:
        discount = int(message.text.strip())

        if discount <= 0 or discount > 100:
            await message.answer("❌ Процент должен быть от 1 до 100. Попробуй ещё раз:")
            return

        await state.update_data(floor_discount_percent=discount)

        # Переход к подтверждению
        await show_rule_confirmation(message, state)

    except ValueError:
        await message.answer("❌ Некорректный процент. Введи целое число, например: 10")


async def show_rule_confirmation(message: Message, state: FSMContext):
    """Показывает резюме правила для подтверждения."""
    data = await state.get_data()

    collection_name = data.get("collection_name", "N/A")
    model = data.get("model")
    condition_type = data.get("condition_type")
    target_price = data.get("target_price")
    floor_discount = data.get("floor_discount_percent")

    text = "✅ Новое правило отслеживания\n\n"
    text += f"Коллекция: **{collection_name}**\n"

    if model:
        text += f"Модель: **{model}**\n"
    else:
        text += "Модель: любая\n"

    text += "\nУсловие:\n"

    if condition_type == ConditionType.FIXED_PRICE:
        text += f"• цена ≤ **{target_price} TON**\n"
    elif condition_type == ConditionType.FLOOR_DISCOUNT:
        text += f"• цена ≤ floor − **{floor_discount}%**\n"

    text += "\nРежим: **только уведомления**\n\n"
    text += "Создать это правило?"

    await message.answer(text, reply_markup=get_rule_confirmation_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == "rule:confirm_create")
async def confirm_create_rule(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание правила."""
    data = await state.get_data()
    user_id = callback.from_user.id

    try:
        # Создаём объект правила
        rule = TrackingRule(
            user_id=user_id,
            collection_name=data.get("collection_name"),
            model=data.get("model"),
            condition_type=data.get("condition_type"),
            target_price=data.get("target_price"),
            floor_discount_percent=data.get("floor_discount_percent"),
            is_active=True
        )

        # Сохраняем в БД
        rule_repo = TrackingRuleRepository()
        rule_id = await rule_repo.create(rule)

        text = (
            "✔️ Правило создано.\n\n"
            f"ID правила: #{rule_id}\n\n"
            "Можешь посмотреть все свои отслеживания командой /my"
        )

        await callback.message.edit_text(text, reply_markup=get_rule_created_keyboard())
        await callback.answer("✅ Правило создано!")
        await state.clear()

    except Exception as e:
        logger.error(f"Error creating rule: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при создании правила", show_alert=True)


@router.callback_query(F.data == "rule:edit")
async def edit_rule(callback: CallbackQuery, state: FSMContext):
    """Редактирование правила (возврат к началу)."""
    await callback.answer("Редактирование пока не реализовано. Начни заново /start")
    await state.clear()


def register_add_tracking_handlers(dp):
    """Регистрирует хэндлеры добавления правил."""
    dp.include_router(router)