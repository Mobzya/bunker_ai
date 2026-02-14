import sqlite3
import re
import datetime
from typing import List, Tuple, Optional
from .config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                class_name TEXT,
                profile TEXT,
                notify INTEGER DEFAULT 1
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                profile TEXT,
                day TEXT NOT NULL,
                lesson_number INTEGER NOT NULL,
                subject TEXT NOT NULL,
                room TEXT NOT NULL,
                UNIQUE(class_name, profile, day, lesson_number)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS sent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                lesson_number INTEGER,
                UNIQUE(user_id, date, lesson_number)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS replacements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                lesson_number INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                teacher TEXT,
                room TEXT,
                UNIQUE(date, class_name, lesson_number)
            )
        ''')
        conn.commit()

# ========== РАСПИСАНИЕ ==========

def add_schedule(class_name: str, profile: Optional[str], day: str, lesson_number: int, subject: str, room: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO schedule (class_name, profile, day, lesson_number, subject, room)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (class_name, profile, day, lesson_number, subject, room))
        conn.commit()

def clear_schedule():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM schedule')
        conn.commit()

def get_classes_with_profiles() -> List[Tuple[str, Optional[str]]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT class_name, profile FROM schedule ORDER BY class_name, profile')
        return cur.fetchall()

def get_parallels() -> List[str]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT class_name FROM schedule')
        rows = cur.fetchall()
    parallels = set()
    for (class_name,) in rows:
        m = re.match(r'^(\d+)', class_name)
        if m:
            parallels.add(m.group(1))
    return sorted(parallels, key=lambda x: int(x))

def get_letters_by_parallel(parallel: str) -> List[str]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT DISTINCT class_name FROM schedule WHERE class_name LIKE ?', (parallel + '%',))
        rows = cur.fetchall()
    letters = []
    for (class_name,) in rows:
        m = re.match(r'^\d+([а-яА-Я]+)', class_name)
        if m:
            letters.append(m.group(1))
    return sorted(letters)

def get_schedule(class_name: str, profile: Optional[str], day: Optional[str] = None) -> List[Tuple]:
    with get_connection() as conn:
        cur = conn.cursor()
        if day:
            cur.execute('''
                SELECT lesson_number, subject, room FROM schedule
                WHERE class_name = ? AND profile IS ? AND day = ?
                ORDER BY lesson_number
            ''', (class_name, profile, day))
        else:
            cur.execute('''
                SELECT day, lesson_number, subject, room FROM schedule
                WHERE class_name = ? AND profile IS ?
                ORDER BY day, lesson_number
            ''', (class_name, profile))
        return cur.fetchall()

# ========== ПОЛЬЗОВАТЕЛИ ==========

def set_user(user_id: int, class_name: str, profile: Optional[str]):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (user_id, class_name, profile, notify) VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET class_name=excluded.class_name, profile=excluded.profile
        ''', (user_id, class_name, profile))
        conn.commit()

def get_user(user_id: int) -> Optional[Tuple[str, Optional[str]]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT class_name, profile FROM users WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        return row if row else None

# ========== УВЕДОМЛЕНИЯ ==========

def get_all_users_with_notify() -> List[Tuple[int, str, Optional[str]]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT user_id, class_name, profile FROM users WHERE notify = 1')
        return cur.fetchall()

def set_notify(user_id: int, enabled: bool):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('UPDATE users SET notify = ? WHERE user_id = ?', (1 if enabled else 0, user_id))
        conn.commit()

def get_notify_status(user_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT notify FROM users WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        return bool(row[0]) if row else False

def mark_notification_sent(user_id: int, lesson_number: int):
    date = datetime.date.today().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT OR IGNORE INTO sent_notifications (user_id, date, lesson_number)
            VALUES (?, ?, ?)
        ''', (user_id, date, lesson_number))
        conn.commit()

def check_notification_sent(user_id: int, lesson_number: int) -> bool:
    date = datetime.date.today().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT 1 FROM sent_notifications
            WHERE user_id = ? AND date = ? AND lesson_number = ?
        ''', (user_id, date, lesson_number))
        return cur.fetchone() is not None

# ========== ЗАМЕНЫ ==========

def add_replacement(date: str, lesson_number: int, class_name: str, subject: str, teacher: Optional[str], room: Optional[str]):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO replacements (date, lesson_number, class_name, subject, teacher, room)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, lesson_number, class_name, subject, teacher, room))
        conn.commit()

def clear_old_replacements(before_date: str):
    """Удалить замены раньше указанной даты (включительно)"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM replacements WHERE date <= ?', (before_date,))
        conn.commit()

def get_replacements_for_date(date: str) -> List[Tuple[int, str, str, Optional[str], Optional[str]]]:
    """Возвращает список замен на конкретную дату: (урок, класс, предмет, учитель, кабинет)"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT lesson_number, class_name, subject, teacher, room
            FROM replacements
            WHERE date = ?
            ORDER BY class_name, lesson_number
        ''', (date,))
        return cur.fetchall()

def get_replacements_for_date_and_class(date: str, class_name: str) -> dict[int, tuple[Optional[str], Optional[str]]]:
    """
    Возвращает словарь замен для конкретной даты и класса:
    ключ = номер урока, значение = (учитель, кабинет)
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT lesson_number, teacher, room
            FROM replacements
            WHERE date = ? AND class_name = ?
        ''', (date, class_name))
        rows = cur.fetchall()
    return {row[0]: (row[1], row[2]) for row in rows}

def get_all_future_replacements() -> List[Tuple[str, int, str, str, Optional[str], Optional[str]]]:
    """Возвращает все будущие замены (начиная с сегодня)"""
    today = datetime.date.today().isoformat()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT date, lesson_number, class_name, subject, teacher, room
            FROM replacements
            WHERE date >= ?
            ORDER BY date, class_name, lesson_number
        ''', (today,))
        return cur.fetchall()