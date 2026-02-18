import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from scripts.update_replacements import update_replacements
from scripts.update_schedule import update_schedule

logger = logging.getLogger(__name__)

def setup_scheduler():
    """Настраивает и возвращает планировщик задач"""
    scheduler = AsyncIOScheduler()

    # Обновление замен каждый день в 3:00
    scheduler.add_job(
        update_replacements,
        trigger=CronTrigger(hour="*/4"),
        id="update_replacements_daily",
        name="Ежедневное обновление замен",
        replace_existing=True,
        misfire_grace_time=36000  # даём час на выполнение, если бот был выключен
    )
    logger.info("Запланировано ежедневное обновление замен в 3:00")

    # Обновление расписания каждые 4 дня в 3:00
    scheduler.add_job(
        update_schedule,
        trigger=CronTrigger(hours="/*8"),
        id="update_schedule_every_4_days",
        name="Обновление расписания раз в 4 дня",
        replace_existing=True,
        misfire_grace_time=36000
    )
    logger.info("Запланировано обновление расписания каждые 4 дня в 3:00")

    return scheduler