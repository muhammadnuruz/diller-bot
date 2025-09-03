import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.dispatcher import bot, dp
from bot.functions import run_main_function
from bot.functions.send_daily_advert import send_daily_advert_function
from bot.handlers.start import router as start_router
from bot.handlers.create_cards import router as card_router
from bot.handlers.ordering import router as order_router
from bot.handlers.display_orders import router as display_router
from bot.handlers.adverb import router as adverb_router
from bot.handlers.give_permission import router as permission_router
from bot.handlers.send_order import router as send_order_router
from bot.handlers.send_adverb import router as send_adverb_router

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

INTERVAL = 5 * 60


async def background_task():
    while True:
        try:
            asyncio.create_task(run_main_function())
        except Exception as e:
            logger.exception("❌ Error executing background task: {}".format(e))
        await asyncio.sleep(INTERVAL)


def setup_routers():
    dp.include_router(start_router)
    dp.include_router(card_router)
    dp.include_router(order_router)
    dp.include_router(display_router)
    dp.include_router(adverb_router)
    dp.include_router(permission_router)
    dp.include_router(send_order_router)
    dp.include_router(send_adverb_router)


async def main():
    setup_routers()
    asyncio.create_task(background_task())
    logger.warning("🤖 Telegram bot launched")
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(send_daily_advert_function, "cron", hour=8, minute=0)
    scheduler.start()

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"❌ An error occurred in the bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
