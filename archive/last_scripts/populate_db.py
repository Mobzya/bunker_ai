import csv
import re
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.db import init_db, clear_schedule, add_schedule
from bot.config import DATA_DIR

def extract_class_info(cell: str):
    """
    Из ячейки вида "10а (техн)" или "5а" извлекает имя класса и профиль.
    Возвращает (class_name, profile), где profile может быть None.
    """
    cell = cell.strip()
    # Ищем паттерн: цифра, буква, затем в скобках профиль
    match = re.match(r'(\d+[а-яА-Я]+)\s*(?:\(([^)]+)\))?', cell)
    if match:
        class_name = match.group(1).strip()
        profile = match.group(2).strip() if match.group(2) else None
        return class_name, profile
    return cell, None

def find_header_row(rows):
    """
    Ищет строку, содержащую названия классов (например, "5а", "5е", "5и").
    Возвращает (index, classes_list), где classes_list — список словарей:
        {
            'name': '5а',
            'profile': None или 'техн',
            'subject_idx': индекс колонки с названием класса (там будет предмет),
            'room_idx': индекс колонки с кабинетом (сразу после subject_idx)
        }
    """
    class_pattern = re.compile(r'\d+[а-яА-Я]')
    for i, row in enumerate(rows):
        if not row:
            continue
        classes = []
        for j, cell in enumerate(row):
            if class_pattern.search(cell):
                # Проверим, что это действительно класс, а не часть другого текста
                if 'каб' not in cell.lower():
                    class_name, profile = extract_class_info(cell)
                    # Предполагаем, что кабинет находится в следующей колонке
                    classes.append({
                        'name': class_name,
                        'profile': profile,
                        'subject_idx': j,
                        'room_idx': j + 1
                    })
        if classes:
            return i, classes
    return None, None

def parse_generic(filepath, filename):
    """
    Универсальная функция для парсинга любого файла с расписанием,
    где после дня и номера урока идут пары предмет-кабинет для каждого класса.
    Возвращает количество добавленных записей.
    """
    print(f"Обработка файла: {filename}")
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Находим строку с классами
    header_idx, classes = find_header_row(rows)
    if not classes:
        print(f"  Не удалось найти классы в файле, пропускаем.")
        return 0

    print(f"  Найдены классы: {[c['name'] for c in classes]}")

    # Находим первую строку с днём недели после заголовка
    days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница']
    start_idx = None
    for i in range(header_idx + 1, len(rows)):
        if rows[i] and rows[i][0] and rows[i][0].strip() in days:
            start_idx = i
            break

    if start_idx is None:
        print(f"  Не найден день недели.")
        return 0

    current_day = None
    total_added = 0
    i = start_idx
    while i < len(rows):
        row = rows[i]
        if not row:
            i += 1
            continue

        # Проверка начала нового дня
        if row[0] and row[0].strip() in days:
            current_day = row[0].strip()
            i += 1
            continue

        # Проверка строки с уроком (вторая колонка содержит номер урока)
        if len(row) > 1 and row[1].strip().isdigit():
            lesson_num = int(row[1].strip())
            for cls in classes:
                subject_idx = cls['subject_idx']
                room_idx = cls['room_idx']
                subject = row[subject_idx].strip() if subject_idx < len(row) else ''
                room = row[room_idx].strip() if room_idx < len(row) else ''
                if subject and subject.lower() not in ['', 'каб', 'предмет']:
                    add_schedule(cls['name'], cls['profile'], current_day, lesson_num, subject, room)
                    total_added += 1
            i += 1
        else:
            # Если строка не содержит номер урока, пропускаем (пустые разделители)
            i += 1

    print(f"  Добавлено записей: {total_added}")
    return total_added

# Отдельные функции для каждого класса (для удобства отладки)
def parse_5():
    filepath = os.path.join(DATA_DIR, "5 классы.csv")
    if os.path.exists(filepath):
        return parse_generic(filepath, "5 классы.csv")
    else:
        print("Файл 5 классы.csv не найден")
        return 0

def parse_6():
    filepath = os.path.join(DATA_DIR, "6 классы.csv")
    if os.path.exists(filepath):
        return parse_generic(filepath, "6 классы.csv")
    else:
        print("Файл 6 классы.csv не найден")
        return 0

def parse_7():
    filepath = os.path.join(DATA_DIR, "7 классы.csv")
    if os.path.exists(filepath):
        return parse_generic(filepath, "7 классы.csv")
    else:
        print("Файл 7 классы.csv не найден")
        return 0

def parse_8():
    filepath = os.path.join(DATA_DIR, "8 классы.csv")
    if os.path.exists(filepath):
        return parse_generic(filepath, "8 классы.csv")
    else:
        print("Файл 8 классы.csv не найден")
        return 0

def parse_9():
    filepath = os.path.join(DATA_DIR, "9 классы.csv")
    if os.path.exists(filepath):
        return parse_generic(filepath, "9 классы.csv")
    else:
        print("Файл 9 классы.csv не найден")
        return 0

def parse_10():
    filepath = os.path.join(DATA_DIR, "10 классы.csv")
    if os.path.exists(filepath):
        return parse_generic(filepath, "10 классы.csv")
    else:
        print("Файл 10 классы.csv не найден")
        return 0

def parse_11():
    filepath = os.path.join(DATA_DIR, "11 классы.csv")
    if os.path.exists(filepath):
        return parse_generic(filepath, "11 классы.csv")
    else:
        print("Файл 11 классы.csv не найден")
        return 0

def populate_all():
    init_db()
    clear_schedule()
    print("База данных очищена.\n")

    total = 0
    total += parse_5()
    total += parse_6()
    total += parse_7()
    total += parse_8()
    total += parse_9()
    total += parse_10()
    total += parse_11()

    print(f"\nВсего добавлено записей: {total}")

if __name__ == "__main__":
    populate_all()