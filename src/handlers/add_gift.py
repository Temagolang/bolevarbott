"""Хэндлеры для добавления подарков."""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.repositories import GiftRepository
from src.services import PortalsService

logger = logging.getLogger(__name__)

router = Router()


class AddGift(StatesGroup):
    """Состояния FSM для добавления подарка."""

    waiting_name = State()
    waiting_model = State()


@router.message(Command("add"))
async def add_start(message: Message, state: FSMContext):
    """Начало добавления подарка."""
    await message.answer("Введите название подарка (name):")
    await state.set_state(AddGift.waiting_name)


@router.message(AddGift.waiting_name)
async def add_name(message: Message, state: FSMContext):
    """Обработка названия подарка."""
    await state.update_data(gift_name=message.text)
    await message.answer("Введите модель подарка (model):")
    await state.set_state(AddGift.waiting_model)


@router.message(AddGift.waiting_model)
async def add_model(message: Message, state: FSMContext):
    """Обработка модели и поиск подарка."""
    data = await state.get_data()
    gift_name = data["gift_name"]
    model = message.text

    portals_service = PortalsService()
    gift_repo = GiftRepository()

    try:
        gift = await portals_service.get_gift_data(gift_name, model, message.from_user.id)

        if not gift:
            await message.answer(f"❌ Подарок '{gift_name}' с моделью '{model}' не найден")
            await state.clear()
            return

        await gift_repo.add_or_update(gift)

        caption = (
            f"✅ Подарок добавлен для отслеживания\n\n"
            f"Название: {gift.name}\n"
            f"Модель: {model}\n"
            f"Цена: {gift.price}\n"
            f"Флор: {gift.floor_price}\n"
            f"Редкость: {gift.model_rarity or 'N/A'}"
        )

        keyboard = None
        if gift.gift_id:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Открыть в Portals",
                            url=f"https://t.me/portals?startapp=gift-{gift.gift_id}",
                        )
                    ]
                ]
            )

        if gift.photo_url:
            try:
                await message.answer_photo(
                    photo=gift.photo_url, caption=caption, reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Error sending photo: {e}")
                await message.answer(caption, reply_markup=keyboard)
        else:
            await message.answer(caption, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error in add_model: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка поиска: {str(e)}")

    await state.clear()


def register_add_gift_handlers(dp):
    """Регистрирует хэндлеры для добавления подарков."""
    dp.include_router(router)