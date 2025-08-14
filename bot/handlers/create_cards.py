from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.buttons.functions import create_cards_function

router = Router()


@router.callback_query(F.data.startswith("category_"))
async def create_cards_handler(call: CallbackQuery):
    await create_cards_function(call=call)