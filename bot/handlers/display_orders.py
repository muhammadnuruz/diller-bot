import aiohttp
import pytz
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from calendar import monthrange

from bot.buttons.inline_buttons import main_menu_button, new_order_button
from bot.buttons.text import my_orders
from bot.functions import build_order_text
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
        await call.message.answer("Вы не приобрели ежемесячную подписку ✖")
        return

    current_year = datetime.now().year
    years = [str(y) for y in range(2020, current_year + 1)]

    kb = InlineKeyboardBuilder()
    for y in years:
        kb.button(text=y, callback_data=f"orders_year:{y}")
    kb.adjust(4)

    await call.message.answer("📅 Выберите год:", reply_markup=kb.as_markup())
    await call.message.delete()


@router.callback_query(F.data.startswith("orders_year:"))
async def year_selected(call: CallbackQuery):
    _, year_str = call.data.split(":")
    year = int(year_str)

    months = [f"{m:02d}" for m in range(1, 13)]

    kb = InlineKeyboardBuilder()
    for m in months:
        kb.button(text=m, callback_data=f"orders_month:{year}-{m}")
    kb.adjust(4)

    await call.message.answer(f"📆 Выберите месяц ({year}):", reply_markup=kb.as_markup())
    await call.message.delete()


@router.callback_query(F.data.startswith("orders_month:"))
async def month_selected(call: CallbackQuery):
    _, month_str = call.data.split(":")
    year, month = map(int, month_str.split("-"))

    _, num_days = monthrange(year, month)
    days = [f"{d:02d}" for d in range(1, num_days + 1)]

    kb = InlineKeyboardBuilder()
    for d in days:
        kb.button(text=d, callback_data=f"orders_day:{year}-{month:02d}-{d}")
    kb.adjust(7)

    await call.message.answer(f"📆 Выберите день ({month_str}):", reply_markup=kb.as_markup())
    await call.message.delete()


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
                    "dateCreate": {
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
    if data['pagination']['total'] < 1:
        await call.answer("❌ В этот день заказов нет.", show_alert=True)
        return

    async with aiohttp.ClientSession() as session:
        for order in orders['order']:
            payload = {
                "auth": {"userId": user_id, "token": token},
                "method": "getClient",
                "params": {
                    "page": 1,
                    "limit": 1000,
                    "filter": {"client": {"CS_id": order['client']['CS_id']}}
                }
            }
            async with session.post(tg_user[0].url, json=payload) as user_resp:
                user_data = await user_resp.json()

            client_data = {}
            if user_data.get("status") and user_data.get("result", {}).get("client"):
                client_data = user_data["result"]["client"][0]
            payload = {
                "auth": {
                    "userId": user_id,
                    "token": token
                },
                "method": "getAgent",
                "params": {
                    "page": 1,
                    "limit": 1000
                }
            }
            related_agent = {
                "CS_id": order.get("agent", {}).get("CS_id", "—"),
                "name": "Информация об агенте не найдена"
            }
            async with session.post(tg_user[0].url, json=payload) as agent_resp:
                agent_data = await agent_resp.json()
            if agent_data.get("status") and agent_data.get("result", {}).get("agent"):
                agents = agent_data["result"]["agent"]
            for agent in agents:
                if agent.get("CS_id") == order.get("agent", {}).get("CS_id"):
                    related_agent = {
                        "CS_id": agent.get("CS_id", "—"),
                        "name": agent.get("name", "—")
                    }

            text = build_order_text(order, client_data, related_agent)
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
