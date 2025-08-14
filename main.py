import asyncio
import logging

from bot.dispatcher import bot, dp
from bot.handlers.start import router as start_router
from bot.handlers.create_cards import router as card_router
from bot.handlers.ordering import router as order_router
from bot.handlers.display_orders import router as display_router

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def setup_routers():
    dp.include_router(start_router)
    dp.include_router(card_router)
    dp.include_router(order_router)
    dp.include_router(display_router)


async def main():
    setup_routers()
    logger.warning("🤖 Telegram bot launched")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"❌ An error occurred in the bot: {e}")


if __name__ == "__main__":
    asyncio.run(main())
