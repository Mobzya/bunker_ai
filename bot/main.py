import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web  # добавить импорт

from bot.config import BOT_TOKEN
from bot.db import init_db
from bot.handlers import start, schedule, notify
from bot.notifier import notification_worker
from bot.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Обработчик для HTTP-запросов (чтобы Render видел открытый порт)
async def handle_health(request):
    return web.Response(text="OK")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle_health)        # можно добавить и другие пути
    app.router.add_get('/health', handle_health)

    port = int(os.environ.get("PORT", 10000))     # Render передаёт PORT
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"HTTP-сервер запущен на порту {port}")

async def main():
    logger.info("Запуск бота")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(schedule.router)
    dp.include_router(notify.router)

    init_db()
    scheduler = setup_scheduler()
    scheduler.start()

    # Запускаем HTTP-сервер (не блокируя основной цикл)
    asyncio.create_task(run_web_server())

    # Запускаем фоновую задачу уведомлений
    asyncio.create_task(notification_worker(bot))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())