import csv
import requests
import sys
import os
import re
import chardet
import logging
from io import StringIO, BytesIO

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

        if row[0] and row[0].strip() in days:
            current_day = row[0].strip()
            i += 1
            continue

        if len(row) > 1 and row[1].strip().isdigit():
            lesson_num = int(row[1].strip())
            for cls in classes:
                subj_idx = cls['subject_idx']
                room_idx = cls['room_idx']
                subject = row[subj_idx].strip() if subj_idx < len(row) else ''
                room = row[room_idx].strip() if room_idx < len(row) else ''
                if subject and subject.lower() not in ['', 'каб', 'предмет']:
                    add_schedule(cls['name'], cls['profile'], current_day, lesson_num, subject, room)
                    added += 1
            i += 1
        else:
            i += 1

    return added

def update_all_schedules():
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
            
            # Отладка: покажем несколько первых строк для проверки
            logger.debug("Первые 5 строк после декодирования:")
            for idx, row in enumerate(rows[:5]):
                logger.debug(f"{idx}: {row}")
            
            added = parse_schedule_data(rows, f"{class_num} класс")
            logger.info(f"Добавлено записей для {class_num} класса: {added}")
            total_added += added
        except Exception as e:
            logger.exception(f"Ошибка при обработке {class_num} класса: {e}")

    logger.info(f"\nВсего добавлено записей: {total_added}")

if __name__ == "__main__":
    update_all_schedules()