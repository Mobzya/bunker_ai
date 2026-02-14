from datetime import datetime

def format_class_display(class_name: str, profile: str | None) -> str:
    if profile:
        return f"{class_name} ({profile})"
    return class_name

def format_lesson_with_replacement(lesson_num: int, subject: str, room: str, repl_info: tuple | None) -> str:
    """
    Форматирует строку урока с учётом замены.
    repl_info: (teacher, room) или None
    """
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
    """Преобразует дату из формата YYYY-MM-DD в DD.MM"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d.%m")
    except:
        return date_str