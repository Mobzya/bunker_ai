from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import datetime
import logging

from bot.keyboards import (
    get_parallels_keyboard,
    get_letters_keyboard,
    get_profiles_keyboard,
    get_main_keyboard
)
from bot.db import (
    get_parallels,
    get_letters_by_parallel,
    get_classes_with_profiles,
    set_user,
    get_user,
    get_notify_status,
    get_schedule,
    get_replacements_for_date_and_class  # добавили импорт
)
from bot.utils import format_class_display, get_current_next_lesson, format_main_menu_text
from bot.config import WEEKDAY_MAP

logger = logging.getLogger(__name__)

router = Router()

class ClassChoice(StatesGroup):
    waiting_for_parallel = State()
    waiting_for_letter = State()
    waiting_for_profile = State()

async def send_main_menu(target, user_id, user_name):
    user_data = get_user(user_id)
    if not user_data:
        logger.info(f"Пользователь {user_id} не выбрал класс, предлагаем выбор")
        parallels = get_parallels()
        if isinstance(target, Message):
            await target.answer(
                "Выбери цифру класса:",
                reply_markup=get_parallels_keyboard(parallels)
            )
        else:
            await target.message.edit_text(
                "Выбери цифру класса:",
                reply_markup=get_parallels_keyboard(parallels)
            )
            await target.answer()
        return

    class_name, profile = user_data
    class_display = format_class_display(class_name, profile)
    logger.debug(f"Пользователь {user_id}, класс {class_display}")

    today_name = WEEKDAY_MAP[datetime.datetime.today().weekday()]
    today_str = datetime.datetime.today().strftime("%Y-%m-%d")
    schedule_today = get_schedule(class_name, profile, today_name)
    replacements = get_replacements_for_date_and_class(today_str, class_name)  # получили замены

    current_info, next_info = get_current_next_lesson(schedule_today, replacements)

    text = format_main_menu_text(
        user_name=user_name,
        class_display=class_display,
        current_info=current_info,
        next_info=next_info,
        no_lessons_message="😴 Сегодня уроков нет."
    )

    notify_enabled = get_notify_status(user_id)

    if isinstance(target, Message):
        await target.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard(notify_enabled))
    else:
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_keyboard(notify_enabled))
        await target.answer()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    logger.info(f"Команда /start от пользователя {user_id} ({user_name})")
    await send_main_menu(message, user_id, user_name)

@router.callback_query(ClassChoice.waiting_for_parallel, F.data.startswith("parallel_"))
async def parallel_chosen(callback: CallbackQuery, state: FSMContext):
    parallel = callback.data.replace("parallel_", "")
    logger.info(f"Пользователь {callback.from_user.id} выбрал параллель {parallel}")
    letters = get_letters_by_parallel(parallel)
    if not letters:
        logger.warning(f"Для параллели {parallel} нет классов")
        await callback.answer("Для этой параллели нет классов", show_alert=True)
        return
    await state.update_data(chosen_parallel=parallel)
    await state.set_state(ClassChoice.waiting_for_letter)
    await callback.message.edit_text(
        "Выбери букву класса:",
        reply_markup=get_letters_keyboard(letters, parallel)
    )
    await callback.answer()

@router.callback_query(ClassChoice.waiting_for_letter, F.data.startswith("letter_"))
async def letter_chosen(callback: CallbackQuery, state: FSMContext):
    full_class = callback.data.replace("letter_", "")
    logger.info(f"Пользователь {callback.from_user.id} выбрал класс {full_class}")
    classes_with_profiles = get_classes_with_profiles()
    profiles = [p for c, p in classes_with_profiles if c == full_class and p is not None]
    if profiles:
        profile = sorted(profiles)[0]
    else:
        profile = None
    set_user(callback.from_user.id, full_class, profile)
    await send_main_menu(callback, callback.from_user.id, callback.from_user.first_name or "Пользователь")
    await state.clear()

@router.callback_query(ClassChoice.waiting_for_profile, F.data.startswith("profile_"))
async def profile_chosen(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 2)
    if len(parts) != 3:
        logger.error(f"Неверный формат callback_data: {callback.data}")
        await callback.answer("Ошибка выбора профиля", show_alert=True)
        return
    class_name = parts[1]
    profile = parts[2]
    logger.info(f"Пользователь {callback.from_user.id} выбрал класс {class_name} профиль {profile}")
    set_user(callback.from_user.id, class_name, profile)
    await send_main_menu(callback, callback.from_user.id, callback.from_user.first_name or "Пользователь")
    await state.clear()