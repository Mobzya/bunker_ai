from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
    get_notify_status
)
from bot.utils import format_class_display

router = Router()

class ClassChoice(StatesGroup):
    waiting_for_parallel = State()
    waiting_for_letter = State()
    waiting_for_profile = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    if user_data:
        class_name, profile = user_data
        notify_enabled = get_notify_status(user_id)
        await message.answer(
            f"Привет! Твой класс: {format_class_display(class_name, profile)}\nВыбери действие:",
            reply_markup=get_main_keyboard(notify_enabled)
        )
    else:
        parallels = get_parallels()
        await state.set_state(ClassChoice.waiting_for_parallel)
        await message.answer(
            "Выбери цифру класса:",
            reply_markup=get_parallels_keyboard(parallels)
        )

@router.callback_query(ClassChoice.waiting_for_parallel, F.data.startswith("parallel_"))
async def parallel_chosen(callback: CallbackQuery, state: FSMContext):
    parallel = callback.data.replace("parallel_", "")
    letters = get_letters_by_parallel(parallel)
    if not letters:
        await callback.answer("Для этой параллели нет классов", show_alert=True)
        return
    await state.update_data(chosen_parallel=parallel)
    await state.set_state(ClassChoice.waiting_for_letter)
    await callback.message.edit_text(
        f"Выбери букву класса:",
        reply_markup=get_letters_keyboard(letters, parallel)
    )
    await callback.answer()

@router.callback_query(ClassChoice.waiting_for_letter, F.data.startswith("letter_"))
async def letter_chosen(callback: CallbackQuery, state: FSMContext):
    full_class = callback.data.replace("letter_", "")
    classes_with_profiles = get_classes_with_profiles()
    profiles = [p for c, p in classes_with_profiles if c == full_class and p is not None]
    if profiles:
        profile = sorted(profiles)[0]
    else:
        profile = None
    set_user(callback.from_user.id, full_class, profile)
    notify_enabled = get_notify_status(callback.from_user.id)
    await callback.message.edit_text(
        f"Класс {full_class}{f' ({profile})' if profile else ''} сохранён. Выбери действие:",
        reply_markup=get_main_keyboard(notify_enabled)
    )
    await state.clear()
    await callback.answer()

@router.callback_query(ClassChoice.waiting_for_profile, F.data.startswith("profile_"))
async def profile_chosen(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 2)
    if len(parts) != 3:
        await callback.answer("Ошибка выбора профиля", show_alert=True)
        return
    class_name = parts[1]
    profile = parts[2]
    set_user(callback.from_user.id, class_name, profile)
    notify_enabled = get_notify_status(callback.from_user.id)
    await callback.message.edit_text(
        f"Класс {class_name} ({profile}) сохранён. Выбери действие:",
        reply_markup=get_main_keyboard(notify_enabled)
    )
    await state.clear()
    await callback.answer()