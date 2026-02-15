import asyncio
import datetime
import logging
from aiogram import Bot
from bot.db import get_all_users_with_notify, get_schedule, mark_notification_sent, check_notification_sent
from bot.config import WEEKDAY_MAP, LESSON_TIMES

logger = logging.getLogger(__name__)

# Время за сколько минут до урока отправлять уведомление
NOTIFY_BEFORE_MINUTES = 16

def get_next_lesson_start_time(now_time):
    """
    Определяет номер следующего урока и время его начала.
    Возвращает (next_lesson_number, start_time) или (None, None), если уроков больше нет.
    """
    now = datetime.datetime.now().time()
    for i, (start, end) in enumerate(LESSON_TIMES, start=1):
        if now < start:
            # ещё не начался этот урок
            return i, start
        # после окончания урока проверяем следующий
    return None, None

def should_notify_now(now_time):
    next_lesson, next_start = get_next_lesson_start_time(now_time)
    if not next_lesson:
        return None
    notify_time = (datetime.datetime.combine(datetime.date.today(), next_start) -
                    datetime.timedelta(minutes=NOTIFY_BEFORE_MINUTES)).time()
    # Учитываем случай, если notify_time меньше 00:00 (не должно быть)
    if notify_time <= now_time < next_start:
        return next_lesson
    return None

async def notification_worker(bot: Bot):
    logger.info(f"Уведомитель запущен (за {NOTIFY_BEFORE_MINUTES} мин до урока)")
    while True:
        
        try:
            now = datetime.datetime.now()
            # Выходные пропускаем
            if now.weekday() >= 5:
                await asyncio.sleep(60)
                continue

            next_lesson_to_notify = should_notify_now(now.time())
            if next_lesson_to_notify is not None:
                users = get_all_users_with_notify()
                logger.debug(f"Проверка уведомлений для {len(users)} пользователей (урок {next_lesson_to_notify})")
                for user_id, class_name, profile in users:
                    logger.info(f"Обработка user {user_id}, класс {class_name}")
                    if check_notification_sent(user_id, next_lesson_to_notify):
                        logger.info(f"Уведомление для урока {next_lesson_to_notify} уже отправлено user {user_id}")
                        continue

                    today_name = WEEKDAY_MAP[now.weekday()]
                    schedule = get_schedule(class_name, profile, today_name)
                    lesson_info = None
                    for lesson_num, subject, room in schedule:
                        if lesson_num == next_lesson_to_notify:
                            lesson_info = (subject, room)
                            break
                    if lesson_info:
                        logger.info(f"Найден урок {next_lesson_to_notify} для user {user_id}: {subject} {room}")
                        subject, room = lesson_info
                        start_time = LESSON_TIMES[next_lesson_to_notify-1][0].strftime('%H:%M')
                        text = (
                            f"🔔 <b>Скоро урок ({next_lesson_to_notify})</b>\n"
                            f"📚 {subject}\n"
                            f"🚪 Кабинет: {room}\n"
                            f"⏰ Начало в {start_time}\n"
                        )
                        try:
                            await bot.send_message(user_id, text, parse_mode="HTML")
                            mark_notification_sent(user_id, next_lesson_to_notify)
                            logger.info(f"Уведомление отправлено пользователю {user_id} (урок {next_lesson_to_notify})")
                        except Exception as e:
                            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
                    else:
                        logger.info(f"Урок {next_lesson_to_notify} не найден в расписании user {user_id}")
            await asyncio.sleep(60)  # проверка каждую минуту
        except Exception as e:
            logger.exception("Ошибка в notification_worker")
            await asyncio.sleep(60)