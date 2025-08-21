from aiogram import F, Router
from aiogram.types import Message

from bot.buttons.text import turn_off_advert, turn_on_advert
from db.model import TelegramUser

router = Router()


@router.message(F.text == turn_off_advert)
async def turn_off_adverb_handler(msg: Message):
    await msg.answer("Реклама отключена.")
    await TelegramUser.create_or_update(
        chat_id=str(msg.from_user.id),
        status_adverb=False
    )


@router.message(F.text == turn_on_advert)
async def turn_on_adverb_handler(msg: Message):
    await msg.answer("Реклама включена")
    await TelegramUser.create_or_update(
        chat_id=str(msg.from_user.id),
        status_adverb=True
    )
