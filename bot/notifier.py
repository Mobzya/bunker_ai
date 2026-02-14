import asyncio
import datetime
from aiogram import Bot
from bot.db import get_all_users_with_notify, get_schedule, mark_notification_sent, check_notification_sent
from bot.config import WEEKDAY_MAP

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

def get_current_lesson_and_next(now_time):
    for i, (start, end) in enumerate(LESSON_TIMES, start=1):
        if start <= now_time <= end:
            return i, i+1 if i < len(LESSON_TIMES) else None
        if i < len(LESSON_TIMES):
            next_start = LESSON_TIMES[i][0]
            if end <= now_time < next_start:
                return i, i+1
        else:
            if end <= now_time:
                return i, None
    return None, None

async def notification_worker(bot: Bot):
    while True:
        try:
            now = datetime.datetime.now()
            if now.weekday() >= 5:
                await asyncio.sleep(60)
                continue

            current_lesson, next_lesson = get_current_lesson_and_next(now.time())
            if current_lesson is not None and next_lesson is not None:
                users = get_all_users_with_notify()
                for user_id, class_name, profile in users:
                    if check_notification_sent(user_id, current_lesson):
                        continue
                    today_name = WEEKDAY_MAP[now.weekday()]
                    schedule = get_schedule(class_name, profile, today_name)
                    next_info = None
                    for lesson_num, subject, room in schedule:
                        if lesson_num == next_lesson:
                            next_info = (subject, room)
                            break
                    if next_info:
                        subject, room = next_info
                        start_time = LESSON_TIMES[next_lesson-1][0].strftime('%H:%M')
                        text = (
                            f"🔔 Следующий урок ({next_lesson}): {subject}\n"
                            f"Кабинет: {room}\n"
                            f"Начало в {start_time}"
                        )
                        try:
                            await bot.send_message(user_id, text)
                            mark_notification_sent(user_id, current_lesson)
                        except Exception as e:
                            print(f"Ошибка отправки пользователю {user_id}: {e}")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Ошибка в notification_worker: {e}")
            await asyncio.sleep(60)