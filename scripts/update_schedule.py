#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import requests
import sys
import os
import re
import chardet
import logging
from io import StringIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.db import init_db, clear_schedule, add_schedule
from bot.config import SCHEDULE_URLS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_class_info(cell):
    cell = cell.strip()
    match = re.match(r'(\d+[а-яА-Я]+)\s*(?:\(([^)]+)\))?', cell)
    if match:
        class_name = match.group(1).strip()
        profile = match.group(2).strip() if match.group(2) else None
        return class_name, profile
    return cell, None

def download_csv_with_encoding(url):
    logger.info(f"Скачивание: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    content = response.content
    detected = chardet.detect(content)
    encoding = detected.get('encoding', 'utf-8')
    logger.info(f"Определена кодировка: {encoding}")

    try:
        text = content.decode(encoding)
    except UnicodeDecodeError:
        for enc in ['utf-8', 'windows-1251', 'cp1251', 'iso-8859-1']:
            try:
                text = content.decode(enc)
                logger.info(f"Успешно декодировано как {enc}")
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("Не удалось декодировать CSV ни в одной из известных кодировок")
    return text

def parse_schedule_data(rows, source_name):
    class_pattern = re.compile(r'\d+[а-яА-Я]+')
    header_idx = None
    classes = []

    for i, row in enumerate(rows):
        if not row:
            continue
        found = []
        for j, cell in enumerate(row):
            if class_pattern.search(cell) and 'каб' not in cell.lower():
                class_name, profile = extract_class_info(cell)
                found.append({
                    'name': class_name,
                    'profile': profile,
                    'subject_idx': j,
                    'room_idx': j + 1
                })
        if found:
            header_idx = i
            classes = found
            logger.info(f"  Найдены классы: {[c['name'] for c in classes]} в строке {i}")
            break

    if not classes:
        logger.warning(f"  Не удалось найти строку с классами в {source_name}")
        return 0

    days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница']
    start_idx = None
    for i in range(header_idx + 1, len(rows)):
        if rows[i] and rows[i][0] and rows[i][0].strip() in days:
            start_idx = i
            logger.info(f"  Первый день найден: {rows[i][0]} в строке {i}")
            break

    if start_idx is None:
        logger.warning(f"  Не найден день недели в {source_name}")
        return 0

    current_day = None
    added = 0
    i = start_idx

    while i < len(rows):
        row = rows[i]
        if not row:
            i += 1
            continue

        # Проверка: строка является днём?
        day_cell = row[0].strip() if row[0] else ''
        if day_cell in days:
            current_day = day_cell
            logger.debug(f"  Установлен день: {current_day} (строка {i})")

            # Проверяем, есть ли в этой же строке первый урок (во втором столбце)
            if len(row) > 1 and row[1] and row[1].strip().isdigit():
                lesson_num = int(row[1].strip())
                if 1 <= lesson_num <= 8:
                    for cls in classes:
                        subj_idx = cls['subject_idx']
                        room_idx = cls['room_idx']
                        subject = row[subj_idx].strip() if subj_idx < len(row) else ''
                        room = row[room_idx].strip() if room_idx < len(row) else ''
                        if subject and subject.lower() not in ['', 'каб', 'предмет']:
                            add_schedule(cls['name'], cls['profile'], current_day, lesson_num, subject, room)
                            added += 1
                    logger.debug(f"    + обработан первый урок {lesson_num} из строки дня")
            i += 1
            continue

        # Проверка: строка является уроком?
        lesson_num = None
        if row[0] and row[0].strip().isdigit():
            lesson_num = int(row[0].strip())
        elif len(row) > 1 and row[1] and row[1].strip().isdigit():
            lesson_num = int(row[1].strip())

        if lesson_num is not None and 1 <= lesson_num <= 8:
            if current_day is None:
                logger.warning(f"Урок {lesson_num} встретился до указания дня, пропускаем строку {i}")
                i += 1
                continue

            for cls in classes:
                subj_idx = cls['subject_idx']
                room_idx = cls['room_idx']
                subject = row[subj_idx].strip() if subj_idx < len(row) else ''
                room = row[room_idx].strip() if room_idx < len(row) else ''
                if subject and subject.lower() not in ['', 'каб', 'предмет']:
                    add_schedule(cls['name'], cls['profile'], current_day, lesson_num, subject, room)
                    added += 1
            i += 1
            continue

        # Всё остальное пропускаем
        i += 1

    logger.info(f"  Добавлено записей для {source_name}: {added}")
    return added

def update_schedule():
    """Функция для вызова из планировщика или из командной строки"""
    logger.info("="*50)
    logger.info("Начало полного обновления расписания...")
    init_db()
    clear_schedule()

    total_added = 0
    for class_num, url in SCHEDULE_URLS.items():
        logger.info(f"\n--- Обработка {class_num} класса ---")
        try:
            text = download_csv_with_encoding(url)
            csv_data = StringIO(text)
            reader = csv.reader(csv_data)
            rows = list(reader)
            logger.info(f"Скачано строк: {len(rows)}")

            added = parse_schedule_data(rows, f"{class_num} класс")
            logger.info(f"Добавлено записей для {class_num} класса: {added}")
            total_added += added
        except Exception as e:
            logger.exception(f"Ошибка при обработке {class_num} класса: {e}")

    logger.info(f"\nВсего добавлено записей: {total_added}")

def main():
    update_schedule()

if __name__ == "__main__":
    main()