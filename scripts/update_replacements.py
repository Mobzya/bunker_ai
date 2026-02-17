#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import requests
import sys
import os
import logging
from datetime import datetime, timedelta
from io import StringIO

# Добавляем путь к корню проекта для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.db import init_db, add_replacement, clear_old_replacements
from bot.config import REPLACEMENTS_URL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_csv(url):
    logger.info(f"Скачивание данных по URL: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        import chardet
        detected = chardet.detect(response.content)
        encoding = detected.get('encoding', 'utf-8')
        logger.info(f"Определена кодировка: {encoding}")

        content = response.content.decode(encoding, errors='replace').encode('utf-8').decode('utf-8')
        csv_data = StringIO(content)
        reader = csv.reader(csv_data)
        rows = list(reader)
        logger.info(f"Скачано строк: {len(rows)}")
        return rows
    except Exception as e:
        logger.error(f"Ошибка при скачивании: {e}")
        return None

def parse_replacements(rows):
    if not rows:
        return 0

    header_idx = None
    for i, row in enumerate(rows):
        if not row or len(row) == 0:
            continue
        first_cell = row[0].strip()
        if first_cell.startswith('\ufeff'):
            first_cell = first_cell[1:].strip()
        if first_cell == 'дата':
            header_idx = i
            break

    if header_idx is None:
        logger.error("Не найден заголовок таблицы замен")
        for idx, r in enumerate(rows[:10]):
            logger.info(f"Строка {idx}: {r}")
        return 0

    headers = rows[header_idx]
    try:
        date_idx = headers.index('дата')
        lesson_idx = headers.index('урок')
        class_idx = headers.index('Класс')
        subject_idx = headers.index('Предмет')
        teacher_idx = headers.index('Заменяющий учитель')
        room_idx = headers.index('Кабинет')
    except ValueError as e:
        logger.error(f"Не найдена нужная колонка: {e}")
        return 0

    today = datetime.today().date()
    added = 0
    skipped = 0

    for row in rows[header_idx+1:]:
        if len(row) <= max(date_idx, lesson_idx, class_idx, subject_idx):
            continue

        date_str = row[date_idx].strip()
        if not date_str:
            continue

        try:
            if len(date_str) <= 5:
                date_str = f"{date_str}.{datetime.today().year}"
            row_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except ValueError:
            continue

        if row_date < today:
            skipped += 1
            continue

        lesson = row[lesson_idx].strip()
        if not lesson.isdigit():
            continue
        lesson_num = int(lesson)
        class_name = row[class_idx].strip()
        subject = row[subject_idx].strip()
        teacher = row[teacher_idx].strip() if teacher_idx < len(row) else ''
        room = row[room_idx].strip() if room_idx < len(row) else ''

        if teacher and teacher.lower() == 'вакансия':
            teacher = None
        if room and room.lower() == 'каб':
            room = None

        add_replacement(row_date.isoformat(), lesson_num, class_name, subject, teacher, room)
        added += 1

    logger.info(f"Добавлено замен: {added}, пропущено (прошлые или битые): {skipped}")
    return added

def update_replacements():
    """Функция для вызова из планировщика или из командной строки"""
    logger.info("="*50)
    logger.info("Обновление таблицы замен...")
    init_db()
    rows = download_csv(REPLACEMENTS_URL)
    if rows:
        today_str = datetime.today().date().isoformat()
        clear_old_replacements(today_str)
        added = parse_replacements(rows)
        logger.info(f"Обновление завершено. Всего актуальных замен в БД: {added}")
    else:
        logger.error("Не удалось получить данные.")

def main():
    update_replacements()

if __name__ == "__main__":
    main()