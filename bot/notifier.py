import datetime
import asyncio
import logging
from zoneinfo import ZoneInfo
from aiogram import Bot
from bot.db import (
    get_all_users_with_notify, get_schedule, mark_notification_sent,
    check_notification_sent, get_last_notification, set_last_notification
)
from bot.config import WEEKDAY_MAP, LESSON_TIMES, TIMEZONE

logger = logging.getLogger(__name__)
NOTIFY_BEFORE_MINUTES = 16
tz = ZoneInfo(TIMEZONE)

def get_next_lesson_start_time(now_time):
    """Определяет номер следующего урока и время его начала (now_time уже в МСК)."""
    for i, (start, end) in enumerate(LESSON_TIMES, start=1):
        if now_time < start:
            return i, start
    return None, None

def should_notify_now(now_time):
    next_lesson, next_start = get_next_lesson_start_time(now_time)
    if not next_lesson:
        return None
    notify_time = (datetime.datetime.combine(datetime.date.today(), next_start) -
                   datetime.timedelta(minutes=NOTIFY_BEFORE_MINUTES)).time()
    if notify_time <= now_time < next_start:
        return next_lesson
    return None

async def notification_worker(bot: Bot):
    logger.info(f"Уведомитель запущен (за {NOTIFY_BEFORE_MINUTES} мин до урока, часовой пояс {TIMEZONE})")
    while True:
        try:
            now = datetime.datetime.now(tz)
            if now.weekday() >= 5:  # суббота, воскресенье
                await asyncio.sleep(60)
                continue

            next_lesson_to_notify = should_notify_now(now.time())
            if next_lesson_to_notify:
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

                        # --- Удаление предыдущего уведомления ---
                        last_msg_id = get_last_notification(user_id)
                        if last_msg_id:
                            try:
                                await bot.delete_message(chat_id=user_id, message_id=last_msg_id)
                                logger.info(f"Удалено предыдущее уведомление для user {user_id}")
                            except Exception as e:
                                # Если не удалось удалить (сообщение слишком старое или уже удалено), просто логируем
                                logger.debug(f"Не удалось удалить предыдущее уведомление для {user_id}: {e}")
                        # ----------------------------------------
                        try:
                            sent_msg = await bot.send_message(user_id, text, parse_mode="HTML")
                            # Сохраняем ID нового сообщения
                            set_last_notification(user_id, sent_msg.message_id)
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