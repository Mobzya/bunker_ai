import datetime
import logging
from zoneinfo import ZoneInfo
from bot.config import LESSON_TIMES, TIMEZONE

logger = logging.getLogger(__name__)

def format_class_display(class_name: str, profile: str | None) -> str:
    if profile:
        return f"{class_name} ({profile})"
    return class_name

def format_lesson_with_replacement(lesson_num: int, subject: str, room: str, repl_info: tuple | None) -> str:
    base = f"{lesson_num}. {subject} — каб. {room}"
    if repl_info:
        teacher, new_room = repl_info
        parts = []
        if teacher:
            parts.append(f"замена: {teacher}")
        if new_room and new_room.lower() != 'каб':
            parts.append(f"каб. {new_room}")
        if parts:
            base += " (" + ", ".join(parts) + ")"
    return base

def format_date_short(date_str: str) -> str:
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d.%m")
    except:
        return date_str

# ---- Функции для главного меню ----

def get_current_next_lesson(schedule_today, replacements=None):
    """
    schedule_today: список кортежей (lesson_num, subject, room) для сегодня
    replacements: словарь {lesson_num: (teacher, room)} или None
    """
    # Текущее время в московском часовом поясе
    tz = ZoneInfo(TIMEZONE)
    now_time = datetime.datetime.now(tz).time()

    current_lesson_num = None
    next_lesson_num = None

    for i, (start, end) in enumerate(LESSON_TIMES, start=1):
        if start <= now_time <= end:
            current_lesson_num = i
            if i < len(LESSON_TIMES):
                next_lesson_num = i + 1
            break
        if i < len(LESSON_TIMES):
            next_start = LESSON_TIMES[i][0]
            if end <= now_time < next_start:
                next_lesson_num = i + 1
                break
        else:
            if end <= now_time:
                current_lesson_num = None
                next_lesson_num = None

    schedule_dict = {num: (subj, room) for num, subj, room in schedule_today}
    repl_dict = replacements if replacements else {}

    current_info = None
    if current_lesson_num and current_lesson_num in schedule_dict:
        subj, room = schedule_dict[current_lesson_num]
        start, end = LESSON_TIMES[current_lesson_num - 1]
        repl_teacher, repl_room = repl_dict.get(current_lesson_num, (None, None))

        now = datetime.datetime.now(tz)
        start_dt = datetime.datetime.combine(now.date(), start, tzinfo=tz)
        end_dt = datetime.datetime.combine(now.date(), end, tzinfo=tz)

        total_seconds = (end_dt - start_dt).total_seconds()
        elapsed = (now - start_dt).total_seconds()
        progress = min(100, int(elapsed / total_seconds * 100)) if total_seconds > 0 else 0
        remaining_min = max(0, int((end_dt - now).total_seconds() // 60))

        current_info = {
            'number': current_lesson_num,
            'subject': subj,
            'room': room,
            'start': start,
            'end': end,
            'progress': progress,
            'remaining_min': remaining_min,
            'repl_teacher': repl_teacher,
            'repl_room': repl_room
        }

    next_info = None
    if next_lesson_num and next_lesson_num in schedule_dict:
        subj, room = schedule_dict[next_lesson_num]
        start, end = LESSON_TIMES[next_lesson_num - 1]
        repl_teacher, repl_room = repl_dict.get(next_lesson_num, (None, None))

        next_info = {
            'number': next_lesson_num,
            'subject': subj,
            'room': room,
            'start': start,
            'end': end,
            'repl_teacher': repl_teacher,
            'repl_room': repl_room
        }

    return current_info, next_info

def format_lesson_block(lesson_info, is_current=False):
    if not lesson_info:
        return ""
    number = lesson_info['number']
    subject = lesson_info['subject']
    room = lesson_info['room']
    start = lesson_info['start'].strftime('%H:%M')
    end = lesson_info['end'].strftime('%H:%M')
    repl_teacher = lesson_info.get('repl_teacher')
    repl_room = lesson_info.get('repl_room')

    lines = []
    if is_current:
        lines.append(f"🟢 <b>Сейчас идёт: {number} урок</b>")
    else:
        lines.append(f"⏭ <b>Следующий: {number} урок</b>")

    if repl_teacher or repl_room:
        main_line = f"   📚 <b>{subject}</b>"
        if repl_room and repl_room.lower() not in ['каб', '']:
            main_line += f"  |  🚪 каб. {repl_room} (было {room})"
        else:
            main_line += f"  |  🚪 каб. {room}"
        lines.append(main_line)
        if repl_teacher:
            lines.append(f"   👤 Замена: {repl_teacher}")
    else:
        lines.append(f"   📚 <b>{subject}</b>  |  🚪 каб. {room}")

    lines.append(f"   ⏳ {start} – {end}")

    if is_current:
        progress = lesson_info['progress']
        remaining = lesson_info.get('remaining_min', 0)
        filled = progress // 10
        empty = 10 - filled
        bar = '🟩' * filled + '⬛' * empty
        lines.append(f"   [{bar}] {progress}% (осталось {remaining} мин)")

    return "\n".join(lines)

def format_main_menu_text(user_name, class_display, current_info, next_info, no_lessons_message=""):
    parts = [f"👋 <b>Привет, {user_name}!</b>", f"📌 Твой класс: {class_display}\n"]
    if current_info or next_info:
        if current_info:
            parts.append(format_lesson_block(current_info, is_current=True))
            if next_info:
                parts.append("")
        if next_info:
            parts.append(format_lesson_block(next_info, is_current=False))
    else:
        parts.append(no_lessons_message or "😴 Сегодня уроков нет.")
    return "\n".join(parts)