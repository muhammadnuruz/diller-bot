from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.buttons.inline_buttons import main_menu_button
from bot.buttons.text import my_orders
from bot.handlers.ordering import format_order_message
from db.model import Order, TelegramUser

router = Router()


@router.callback_query(F.data == my_orders)
async def my_orders_handler(call: CallbackQuery):
    tg_user = await TelegramUser.get_by(chat_id=str(call.from_user.id))
    if not tg_user[0].is_purchase:
        await call.message.answer(text="Вы не приобрели ежемесячную подписку ✖")
        return
    orders = await Order.get_by(shop=tg_user[0].id)

    if not orders:
        await call.answer("📦 У вас пока нет заказов.", show_alert=True)
        return

    for order in orders:
        text = format_order_message(order)
        await call.message.answer(text, parse_mode="HTML")

    buttons = await main_menu_button(url=tg_user[0].url, login=tg_user[0].login, password=tg_user[0].password)
    if buttons:
        await call.message.answer(text="Выберите нужную категорию", reply_markup=buttons)
    else:
        await call.message.answer("""
У вас нет категорий или информация неверна.

Чтобы начать заново: /start
""")
