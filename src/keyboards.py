"""Inline клавиатуры для бота."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Возвращает главное меню бота."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить отслеживание", callback_data="menu:add_tracking")],
            [InlineKeyboardButton(text="📋 Мои отслеживания", callback_data="menu:my_trackings")],
        ]
    )


def get_search_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа поиска коллекции."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 По коллекции", callback_data="search:by_collection")],
            [InlineKeyboardButton(text="🔍 По имени подарка", callback_data="search:by_name")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
        ]
    )


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в главное меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="menu:main")],
        ]
    )


def get_condition_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа ценового условия."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="≤ Фиксированная цена", callback_data="condition:fixed_price")],
            [InlineKeyboardButton(text="↓ Ниже floor на %", callback_data="condition:floor_discount")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="add:back_to_model")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ]
    )


def get_rule_actions_keyboard(rule_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """
    Клавиатура действий с правилом.

    Args:
        rule_id: ID правила
        is_active: Активно ли правило
    """
    pause_text = "⏸ Поставить на паузу" if is_active else "▶️ Включить"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=pause_text, callback_data=f"rule:toggle:{rule_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"rule:delete_confirm:{rule_id}")],
            [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="menu:my_trackings")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ]
    )


def get_delete_confirmation_keyboard(rule_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления правила."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"rule:delete:{rule_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"rule:view:{rule_id}"),
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ]
    )


def get_model_selection_keyboard(back_callback: str = "add:skip_model") -> InlineKeyboardMarkup:
    """Клавиатура для выбора модели."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать из списка", callback_data="add:select_model")],
            [InlineKeyboardButton(text="Пропустить", callback_data="add:skip_model")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ]
    )


def get_rule_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения создания правила."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Создать", callback_data="rule:confirm_create")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="rule:edit")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="menu:main")],
        ]
    )


def get_rule_created_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после успешного создания правила."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Мои отслеживания", callback_data="menu:my_trackings")],
            [InlineKeyboardButton(text="➕ Добавить ещё", callback_data="menu:add_tracking")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
        ]
    )


def get_alert_keyboard(lot_url: str, rule_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для уведомления об алерте.

    Args:
        lot_url: Ссылка на лот в Portals
        rule_id: ID правила
    """
    buttons = []

    if lot_url:
        buttons.append([InlineKeyboardButton(text="🔗 Открыть в Portals", url=lot_url)])

    buttons.append([InlineKeyboardButton(text="📋 Открыть правило", callback_data=f"rule:view:{rule_id}")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)