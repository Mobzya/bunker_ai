import os
import datetime

BOT_TOKEN = "8184763713:AAGsjOyZGqLPfq8AbdeQ3GfXahdTSfen8pw"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "schedule.db")
DATA_DIR = os.path.join(BASE_DIR, "data")

DAYS = ["понедельник", "вторник", "среда", "четверг", "пятница"]
WEEKDAY_MAP = {
    0: "понедельник",
    1: "вторник",
    2: "среда",
    3: "четверг",
    4: "пятница",
    5: "суббота",
    6: "воскресенье"
}

# Время уроков (начало, конец)
LESSON_TIMES = [
    (datetime.time(8, 15), datetime.time(9, 0)),
    (datetime.time(9, 15), datetime.time(10, 0)),
    (datetime.time(10, 15), datetime.time(11, 0)),
    (datetime.time(11, 15), datetime.time(12, 0)),
    (datetime.time(12, 15), datetime.time(13, 0)),
    (datetime.time(13, 15), datetime.time(14, 0)),
    (datetime.time(14, 15), datetime.time(15, 0)),
    (datetime.time(15, 15), datetime.time(16, 0)),
]

# --- Ссылки для автоматического обновления ---
REPLACEMENTS_URL = "https://docs.google.com/spreadsheets/d/1ssv52YzwfZ3S-azlDu49_hyLnF-TMJYf3lo-WbdmvI8/export?format=csv&gid=122869822"

SCHEDULE_URLS = {
    "5": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=982486379",
    "6": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=576736158",
    "7": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=875650471",
    "8": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=981088746",
    "9": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=1531352472",
    "10": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=689182908",
    "11": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=932298242",
}