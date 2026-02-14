import os

BOT_TOKEN = "8358936547:AAFqzW9kWXmwXAuAl9k8ZiStY594wVvM0aI" 

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

# --- Ссылки для автоматического обновления ---
# Замены
REPLACEMENTS_URL = "https://docs.google.com/spreadsheets/d/1ssv52YzwfZ3S-azlDu49_hyLnF-TMJYf3lo-WbdmvI8/export?format=csv&gid=122869822"

# Расписание для каждого класса (ID таблицы общий, разные GID)
SCHEDULE_URLS = {
    "5": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=982486379",
    "6": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=576736158",
    "7": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=875650471",
    "8": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=981088746",
    "9": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=1531352472",
    "10": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=689182908",
    "11": "https://docs.google.com/spreadsheets/d/1u117ewxXm5KavaFK2y2UFSOV8Qn5AejrXzNeUG3aIOs/export?format=csv&gid=932298242",
}