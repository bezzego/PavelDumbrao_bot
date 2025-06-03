import asyncio
import config
from db.db import init_db
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import user, lessons, referral, premium, admin
from utils.scheduler import check_payments_job
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
    await bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher(storage=MemoryStorage())
    # Include routers from handlers
    dp.include_router(lessons.router)
    dp.include_router(referral.router)
    dp.include_router(premium.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)
    # Initialize database
    init_db()
    # Set up scheduler for periodic tasks (e.g., payment checking)
    scheduler = AsyncIOScheduler()
    # Check YooMoney payments every 60 seconds
    scheduler.add_job(check_payments_job, "interval", seconds=60, args=(bot,))
    scheduler.start()
    # Start polling
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
