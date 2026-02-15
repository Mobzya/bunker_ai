import csv
import os
import re
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.db import init_db, clear_old_replacements, add_replacement
from bot.config import DATA_DIR

def parse_replacements_file(filepath):
    """
    Парсит файл с заменами, добавляет только будущие замены.
    Ожидается формат: первая строка "дата,урок,Класс,Предмет,Отсутствующий учитель,Основание,Заменяющий учитель,Кабинет,примеч"
    Далее строки с данными.
    """
    print(f"Обработка файла замен: {os.path.basename(filepath)}")
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Найдём заголовок
    header_row = None
    for i, row in enumerate(rows):
        if row and row[0] == 'дата' and len(row) >= 8:
            header_row = i
            break
    if header_row is None:
        print("  Не найден заголовок таблицы замен")
        return

    # Индексы колонок (по заголовку)
    headers = rows[header_row]
    try:
        date_idx = headers.index('дата')
        lesson_idx = headers.index('урок')
        class_idx = headers.index('Класс')
        subject_idx = headers.index('Предмет')
        teacher_idx = headers.index('Заменяющий учитель')
        room_idx = headers.index('Кабинет')
    except ValueError as e:
        print(f"  Ошибка: не найдена нужная колонка: {e}")
        return

    # Получаем сегодняшнюю дату для фильтрации
    today = datetime.today().date()
    added = 0
    skipped = 0

    for row in rows[header_row+1:]:
        if len(row) <= max(date_idx, lesson_idx, class_idx, subject_idx, teacher_idx, room_idx):
            continue
        date_str = row[date_idx].strip()
        if not date_str:
            continue
        # Пытаемся распарсить дату в формате DD.MM.YYYY или DD.MM.YY
        try:
            if len(date_str) <= 5:  # короткая дата типа "16.02"
                # добавим текущий год
                date_str = f"{date_str}.{datetime.today().year}"
            row_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            # пропускаем строки с неправильной датой (заголовки, пустое)
            continue

        if row_date < today:
            skipped += 1
            continue

        # Извлекаем данные
        lesson = row[lesson_idx].strip()
        if not lesson.isdigit():
            continue
        lesson_num = int(lesson)
        class_name = row[class_idx].strip()
        subject = row[subject_idx].strip()
        teacher = row[teacher_idx].strip() if teacher_idx < len(row) else ''
        room = row[room_idx].strip() if room_idx < len(row) else ''
        # Очистим от лишних пробелов
        teacher = teacher if teacher and teacher.lower() != 'вакансия' else None
        room = room if room and room.lower() != 'каб' else None

        # Сохраняем в БД
        add_replacement(row_date.isoformat(), lesson_num, class_name, subject, teacher, room)
        added += 1

    print(f"  Добавлено замен: {added}, пропущено (прошлые): {skipped}")

def main():
    init_db()
    # Очистим старые замены (до сегодня)
    today_str = datetime.today().date().isoformat()
    clear_old_replacements(today_str)  # удаляем всё, что раньше сегодня
    print("Старые замены удалены.")

    filepath = os.path.join(DATA_DIR, "Замена уроков Лицей 2025-2026 уч.год - замена февраль 2026.csv")
    if os.path.exists(filepath):
        parse_replacements_file(filepath)
    else:
        print(f"Файл замен не найден: {filepath}")

if __name__ == "__main__":
    main()