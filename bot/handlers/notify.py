from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging
from bot.db import get_notify_status, set_notify, get_user
from bot.keyboards import get_main_keyboard
from bot.utils import format_class_display

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == "toggle_notify")
async def toggle_notify(callback: CallbackQuery):
    user_id = callback.from_user.id
    current = get_notify_status(user_id)
    new_status = not current
    set_notify(user_id, new_status)
    user_data = get_user(user_id)
    logger.info(f"Пользователь {user_id} переключил уведомления: {new_status}")
    if user_data:
        class_name, profile = user_data
        status_text = "включены" if new_status else "отключены"
        await callback.message.edit_text(
            f"🔔 Уведомления {status_text}.",
            reply_markup=get_main_keyboard(new_status)
        )
    else:
        await callback.message.edit_text(
            "Статус уведомлений изменён.",
            reply_markup=get_main_keyboard(new_status)
        )
    await callback.answer()