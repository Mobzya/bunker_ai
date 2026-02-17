import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.db import init_db
from bot.handlers import start, schedule, notify
from bot.notifier import notification_worker
from bot.scheduler import setup_scheduler  # новый импорт

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiogram.event').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск бота")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(schedule.router)
    dp.include_router(notify.router)

    # Инициализация базы данных
    init_db()

    # Настройка и запуск планировщика
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Планировщик задач запущен")

    # Запуск фоновой задачи уведомлений
    asyncio.create_task(notification_worker(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())