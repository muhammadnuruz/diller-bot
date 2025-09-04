from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

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

    months = sorted({o.created_at.strftime("%Y-%m") for o in orders})
    kb = InlineKeyboardBuilder()
    for m in months:
        kb.button(text=m, callback_data=f"orders_month:{m}")
    kb.adjust(2)

    await call.message.answer("📅 Выберите месяц:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("orders_month:"))
async def month_selected(call: CallbackQuery):
    _, month_str = call.data.split(":")
    year, month = map(int, month_str.split("-"))

    tg_user = await TelegramUser.get_by(chat_id=str(call.from_user.id))
    orders = await Order.get_by(shop=tg_user[0].id)

    days = sorted(
        {o.created_at.strftime("%d") for o in orders if o.created_at.year == year and o.created_at.month == month})

    if not days:
        await call.answer("❌ В этом месяце заказов нет.", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    for d in days:
        kb.button(text=d, callback_data=f"orders_day:{year}-{month:02d}-{d}")
    kb.adjust(5)

    await call.message.answer(f"📆 Выберите день ({month_str}):", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("orders_day:"))
async def day_selected(call: CallbackQuery):
    _, date_str = call.data.split(":")
    year, month, day = map(int, date_str.split("-"))

    tg_user = await TelegramUser.get_by(chat_id=str(call.from_user.id))
    orders = await Order.get_by(shop=tg_user[0].id)

    filtered_orders = [o for o in orders if o.created_at.date() == datetime(year, month, day).date()]

    if not filtered_orders:
        await call.answer("❌ В этот день заказов нет.", show_alert=True)
        return

    for order in filtered_orders:
        text = format_order_message(order)
        await call.message.answer(text, parse_mode="HTML")

    buttons = await main_menu_button(url=tg_user[0].url, login=tg_user[0].login, password=tg_user[0].password)
    if buttons:
        await call.message.answer("Выберите нужную категорию", reply_markup=buttons)
    else:
        await call.message.answer("""
У вас нет категорий или информация неверна.

Чтобы начать заново: /start
""")
