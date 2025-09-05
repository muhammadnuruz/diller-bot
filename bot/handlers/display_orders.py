import aiohttp
import pytz
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from bot.buttons.inline_buttons import main_menu_button, new_order_button
from bot.buttons.text import my_orders
from bot.handlers.ordering import format_order_message
from db.model import TelegramUser

router = Router()


async def get_token_and_id(user):
    async with aiohttp.ClientSession() as session:
        async with session.post(
                user.url,
                json={
                    "method": "login",
                    "auth": {"login": user.login, "password": user.password},
                },
        ) as resp:
            data = await resp.json()

    if data.get("status"):
        return data["result"]["userId"], data["result"]["token"]
    return None, None


@router.callback_query(F.data == my_orders)
async def my_orders_handler(call: CallbackQuery):
    tg_user = await TelegramUser.get_by(chat_id=str(call.from_user.id))
    if not tg_user[0].is_purchase:
        await call.message.answer(text="Вы не приобрели ежемесячную подписку ✖")
        return

    user_id, token = await get_token_and_id(tg_user[0])
    if not user_id:
        await call.answer("Ошибка авторизации ❌", show_alert=True)
        return

    payload = {
        "auth": {"userId": user_id, "token": token},
        "method": "getOrder",
        "params": {
            "page": 1,
            "limit": 1000,
            "filter": {"include": "all", "status": [1, 2, 3]},
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(tg_user[0].url, json=payload) as resp:
            data = await resp.json()

    orders = data.get("result", [])
    if not orders:
        await call.answer("📦 У вас пока нет заказов.", show_alert=True)
        return

    months = sorted({datetime.fromisoformat(o["orderCreated"]).strftime("%Y-%m") for o in orders})

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
    user_id, token = await get_token_and_id(tg_user[0])
    if not user_id:
        await call.answer("Ошибка авторизации ❌", show_alert=True)
        return

    payload = {
        "auth": {"userId": user_id, "token": token},
        "method": "getOrder",
        "params": {
            "page": 1,
            "limit": 1000,
            "filter": {"include": "all", "status": [1, 2, 3]},
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(tg_user[0].url, json=payload) as resp:
            data = await resp.json()

    orders = data.get("result", [])

    days = sorted({
        datetime.fromisoformat(o["orderCreated"]).strftime("%d")
        for o in orders
        if datetime.fromisoformat(o["orderCreated"]).year == year
           and datetime.fromisoformat(o["orderCreated"]).month == month
    })

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
    user_id, token = await get_token_and_id(tg_user[0])
    if not user_id:
        await call.answer("Ошибка авторизации ❌", show_alert=True)
        return

    tz = pytz.timezone("Asia/Tashkent")
    start_date = datetime(year, month, day, 0, 0, 0, tzinfo=tz)
    end_date = datetime(year, month, day, 23, 59, 59, tzinfo=tz)
    date_format = "%Y-%m-%dT%H:%M:%S%z"

    payload = {
        "auth": {"userId": user_id, "token": token},
        "method": "getOrder",
        "params": {
            "page": 1,
            "limit": 1000,
            "filter": {
                "include": "all",
                "status": [1, 2, 3],
                "period": {
                    "orderCreated": {
                        "from": start_date.strftime(date_format),
                        "to": end_date.strftime(date_format),
                    }
                },
            },
        },
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(tg_user[0].url, json=payload) as resp:
            data = await resp.json()

    orders = data.get("result", [])
    if not orders:
        await call.answer("❌ В этот день заказов нет.", show_alert=True)
        return

    for order in orders:
        text = format_order_message(order)
        await call.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=await new_order_button(order["CS_id"])
        )

    buttons = await main_menu_button(
        url=tg_user[0].url,
        login=tg_user[0].login,
        password=tg_user[0].password,
    )
    if buttons:
        await call.message.answer("Выберите нужную категорию", reply_markup=buttons)
    else:
        await call.message.answer("""
У вас нет категорий или информация неверна.

Чтобы начать заново: /start
""")
