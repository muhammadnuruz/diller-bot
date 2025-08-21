from datetime import datetime

from aiogram.types import FSInputFile

from bot.buttons.inline_buttons import buy_cards_button
from bot.dispatcher import bot
from db.model import TelegramUser, Card


async def send_daily_advert_function():
    now = datetime.now()
    day_number = now.weekday() + 1
    telegram_users = await TelegramUser.get_by(day=day_number, status_adverb=True)
    default_image = FSInputFile("image/none_img.png")
    for user in telegram_users:
        for card_id in user.card_ids:
            card = await Card.get_by(unique_link=card_id)
            caption = (
                f"<b>{card[0].name}</b>\n"
                f"💰 Цена: <b>{card[0].price}</b> сум\n"
                f"🆔 Код товара: <code>{card[0].unique_link}</code>"
            )
            await bot.send_photo(chat_id=user.chat_id, photo=default_image, caption=caption, parse_mode="HTML",
                                 reply_markup=await buy_cards_button(card[0].id))
