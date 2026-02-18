from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta
import locale
import logging
from aiogram.fsm.context import FSMContext
from bot.keyboards import get_main_keyboard
from bot.db import (
    get_user,
    get_schedule,
    get_replacements_for_date_and_class,
    get_all_future_replacements,
    get_notify_status,
    get_parallels
)
from bot.config import DAYS, WEEKDAY_MAP
from bot.utils import format_class_display, format_lesson_with_replacement, format_date_short

logger = logging.getLogger(__name__)

router = Router()

# Попытка установить русскую локаль для отображения дней недели
try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    pass

def get_week_dates(base_date: datetime) -> dict[str, str]:
    """
    Возвращает словарь: день недели (строка, нижний регистр) -> дата в формате YYYY-MM-DD
    для дней начиная с base_date (сегодня) и до конца недели (пятница).
    Если base_date уже после пятницы, возвращаем пустой словарь.
    """
    dates = {}
    current = base_date
    while current.weekday() < 5:  # пока не суббота
        day_name = WEEKDAY_MAP[current.weekday()]
        dates[day_name] = current.strftime("%Y-%m-%d")
        current += timedelta(days=1)
    return dates

@router.callback_query(F.data == "today")
async def show_today(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user(user_id)
    if not user_data:
        logger.warning(f"Пользователь {user_id} попытался посмотреть сегодня без выбора класса")
        await callback.message.edit_text(
            "Сначала выбери класс.",
            reply_markup=get_main_keyboard(False)
        )
        await callback.answer()
        return

    class_name, profile = user_data
    today_name = WEEKDAY_MAP[datetime.today().weekday()]
    today_str = datetime.today().strftime("%Y-%m-%d")
    schedule = get_schedule(class_name, profile, today_name)
    replacements = get_replacements_for_date_and_class(today_str, class_name)

    logger.info(f"Пользователь {user_id} запросил расписание на сегодня ({class_name})")

    if not schedule:
        text = f"📭 На {today_name} уроков нет."
    else:
        text = f"📚 <b>Расписание на {today_name}</b> ({format_class_display(class_name, profile)}):\n\n"
        for lesson_num, subject, room in schedule:
            repl_info = replacements.get(lesson_num)
            text += format_lesson_with_replacement(lesson_num, subject, room, repl_info) + "\n"

    notify_enabled = get_notify_status(user_id)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_keyboard(notify_enabled))
    await callback.answer()

@router.callback_query(F.data == "week")
async def show_week(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user(user_id)
    if not user_data:
        logger.warning(f"Пользователь {user_id} попытался посмотреть неделю без выбора класса")
        await callback.message.edit_text(
            "Сначала выбери класс.",
            reply_markup=get_main_keyboard(False)
        )
        await callback.answer()
        return

    class_name, profile = user_data
    schedule = get_schedule(class_name, profile)
    if not schedule:
        logger.info(f"Для пользователя {user_id} расписание не найдено")
        await callback.message.edit_text("Расписание не найдено.", reply_markup=get_main_keyboard(False))
        await callback.answer()
        return

    logger.info(f"Пользователь {user_id} запросил расписание на неделю ({class_name})")

    # Группируем расписание по дням
    by_day = {}
    for day, lesson_num, subject, room in schedule:
        by_day.setdefault(day, []).append((lesson_num, subject, room))

    # Определяем даты для дней недели, начиная с сегодня
    today = datetime.today()
    week_dates = get_week_dates(today)
    # Получаем замены для каждого дня из week_dates
    replacements_by_day = {}
    for day_name, date_str in week_dates.items():
        replacements_by_day[day_name] = get_replacements_for_date_and_class(date_str, class_name)

    text = f"📆 <b>Расписание на неделю</b> для {format_class_display(class_name, profile)}:\n\n"
    for day in DAYS:
        if day in by_day:
            # Если день есть в расписании
            day_header = f"📅 <b>{day.capitalize()}</b>"
            # Если для этого дня известна дата, добавим её
            if day in week_dates:
                day_header += f" ({format_date_short(week_dates[day])})"
            text += day_header + ":\n"

            for lesson_num, subject, room in sorted(by_day[day], key=lambda x: x[0]):
                repl_info = replacements_by_day.get(day, {}).get(lesson_num)
                text += format_lesson_with_replacement(lesson_num, subject, room, repl_info) + "\n"
            text += "\n"
        else:
            text += f"📅 <b>{day.capitalize()}</b>: нет уроков\n\n"

    notify_enabled = get_notify_status(user_id)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_main_keyboard(notify_enabled))
    await callback.answer()

@router.callback_query(F.data == "replacements")
async def show_replacements(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user(user_id)
    if not user_data:
        logger.warning(f"Пользователь {user_id} попытался посмотреть замены без выбора класса")
        await callback.message.edit_text(
            "Сначала выбери класс.",
            reply_markup=get_main_keyboard(False)
        )
        await callback.answer()
        return

    class_name, profile = user_data
    user_class_display = format_class_display(class_name, profile)
    logger.info(f"Пользователь {user_id} запросил замены")

    all_replacements = get_all_future_replacements()

    # Разделяем
    user_repl = []
    other_repl = []
    for repl in all_replacements:
        date, lesson, repl_class, subject, teacher, room = repl
        if repl_class == user_class_display:
            user_repl.append(repl)
        else:
            other_repl.append(repl)

    # Функция построения текста по заданным спискам
    def build_text(user_list, other_list):
        parts = []

        # Блок замен для класса пользователя
        parts.append("<b>🔔 Замены для вашего класса</b>:\n")
        if user_list:
            by_date = {}
            for date, lesson, repl_class, subject, teacher, room in user_list:
                by_date.setdefault(date, []).append((lesson, subject, teacher, room))
            for date in sorted(by_date.keys()):
                parts.append(f"\n📅 {format_date_short(date)}:")
                for lesson, subject, teacher, room in sorted(by_date[date], key=lambda x: x[0]):
                    line = f"  • {lesson} урок — <b>{subject}</b>"
                    if teacher or room:
                        line += " ("
                        if teacher:
                            line += f"👤 {teacher}"
                        if teacher and room:
                            line += ", "
                        if room:
                            line += f"🚪 {room}"
                        line += ")"
                    parts.append(line)
        else:
            parts.append("   Нет замен для вашего класса.")

        # Разделитель
        parts.append("\n\n<b>📌 Остальные замены</b>:\n")

        if other_list:
            by_date = {}
            for date, lesson, repl_class, subject, teacher, room in other_list:
                by_date.setdefault(date, []).append((lesson, repl_class, subject, teacher, room))
            for date in sorted(by_date.keys()):
                parts.append(f"\n📅 {format_date_short(date)}:")
                for lesson, repl_class, subject, teacher, room in sorted(by_date[date], key=lambda x: (x[1], x[0])):
                    line = f"  • {lesson} урок — <b>{repl_class}</b>, {subject}"
                    if teacher or room:
                        line += " ("
                        if teacher:
                            line += f"👤 {teacher}"
                        if teacher and room:
                            line += ", "
                        if room:
                            line += f"🚪 {room}"
                        line += ")"
                    parts.append(line)
        else:
            parts.append("   Нет других замен.")

        return "\n".join(parts)

    # Сначала пробуем полный текст
    full_text = build_text(user_repl, other_repl)
    text_length = len(full_text)

    # Если слишком длинно (с запасом 4000), убираем сегодняшний день
    if text_length > 4000:
        today_str = datetime.now().date().isoformat()
        # Фильтруем, исключая сегодняшнюю дату
        user_repl_filtered = [r for r in user_repl if r[0] != today_str]
        other_repl_filtered = [r for r in other_repl if r[0] != today_str]

        # Пробуем построить текст без сегодня
        filtered_text = build_text(user_repl_filtered, other_repl_filtered)
        if len(filtered_text) > 4000:
            # Всё ещё длинно – дополнительно ограничиваем остальные замены до 10 ближайших
            # Сортируем other_repl_filtered по дате и уроку
            other_repl_filtered.sort(key=lambda x: (x[0], x[1]))
            other_repl_limited = other_repl_filtered[:10]
            filtered_text = build_text(user_repl_filtered, other_repl_limited)
            # Добавляем предупреждение об обрезании
            filtered_text += "\n\n⚠️ <i>Показаны не все замены из-за ограничений длины сообщения.</i>"
        else:
            # Добавляем предупреждение, что убраны замены на сегодня
            filtered_text += "\n\n⚠️ <i>Замены на сегодня не показаны, так как сообщение было слишком длинным.</i>"

        final_text = filtered_text
    else:
        final_text = full_text

    notify_enabled = get_notify_status(user_id)
    await callback.message.edit_text(final_text, parse_mode="HTML", reply_markup=get_main_keyboard(notify_enabled))
    await callback.answer()

@router.callback_query(F.data == "change_class")
async def change_class(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.start import ClassChoice
    from bot.keyboards import get_parallels_keyboard
    logger.info(f"Пользователь {callback.from_user.id} меняет класс")
    parallels = get_parallels()
    await callback.message.edit_text(
        "Выбери новую цифру класса:",
        reply_markup=get_parallels_keyboard(parallels)
    )
    await state.set_state(ClassChoice.waiting_for_parallel)
    await callback.answer()