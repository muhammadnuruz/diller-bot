import uuid

import aiohttp
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, FSInputFile

from bot.buttons.inline_buttons import buy_cards_button
from bot.buttons.reply_buttons import request_user_reply_keyboard, main_menu_reply_buttons
from bot.functions import build_order_text
from bot.functions.new_orders import get_login_task, validate_data, get_agent_tasks
from db.model import TelegramUser, Card

router = Router()


@router.callback_query(F.data.startswith("send:new:order:"))
async def send_order_handler(call: CallbackQuery):
    _, _, _, order_id = call.data.split(":")
    id_ = order_id.split("_")[-1]
    await call.message.answer(
        "📤Кому отправить открытку?",
        reply_markup=request_user_reply_keyboard(int(id_))
    )


@router.message(F.user_shared)
async def handle_user_shared(msg: Message):
    user_shared = msg.user_shared
    user_id_ = user_shared.user_id
    request_id = user_shared.request_id
    try:
        message = await msg.bot.send_message(chat_id=user_id_, text="Test!")
        await message.delete()
    except Exception:
        await msg.answer("Клиент заблокировал бота или не является участником.",
                         reply_markup=await main_menu_reply_buttons())
        return
    cs_id = f"d0_{request_id}"
    tg_user = await TelegramUser.get_by(chat_id=str(msg.from_user.id))
    if not tg_user[0].is_purchase:
        await msg.answer(text="Вы не приобрели ежемесячную подписку ✖", reply_markup=await main_menu_reply_buttons())
        return
    async with aiohttp.ClientSession() as session:
        try:
            login_datas = await validate_data(get_login_task(session, tg_user))
            user_id = login_datas[0]["result"]["userId"]
            token = login_datas[0]["result"]["token"]
        except Exception as e:
            await msg.answer(
                "Пожалуйста, отправьте администратору сообщение об ошибке при входе в систему: {}".format(e))
            return
        try:
            order_resp = await session.post(
                url=tg_user[0].url,
                json={
                    "auth": {
                        "userId": user_id,
                        "token": token
                    },
                    "method": "getOrder",
                    "params": {
                        "page": 1,
                        "limit": 1000
                    }
                }
            )
            order_data = await order_resp.json()
            order = None
            for orders in order_data["result"]["order"]:
                if orders['CS_id'] == cs_id:
                    order = orders
                    break
            if not order:
                return await msg.answer("Заказ не найден ❌", reply_markup=await main_menu_reply_buttons())
        except Exception as e:
            await msg.answer(
                "Пожалуйста, отправьте администратору сообщение об ошибке при получении вашего заказа: {}".format(e))
            return
        try:
            client_resp = await session.post(url=tg_user[0].url, json={
                "auth": {"userId": user_id, "token": token},
                "method": "getClient",
                "params": {
                    "page": 1,
                    "limit": 1000,
                    "filter": {"client": {"CS_id": order['client']['CS_id']}}
                }
            })
            client_data = await client_resp.json()
            client = client_data['result']['client'][0]
            client_day = 1
            if client.get("agents") and client["agents"][0].get("days"):
                client_day = client["agents"][0]["days"][0]
            agents = await validate_data(get_agent_tasks(session, tg_user, login_datas))
            related_agent = {"CS_id": "—", "name": "—"}
            for agent in agents:
                for a in agent.get("result", {}).get("agent", []):
                    if a.get("CS_id") == order.get("agent", {}).get("CS_id"):
                        related_agent = {
                            "CS_id": a.get("CS_id", "—"),
                            "name": a.get("name", "—")
                        }
                        break
            text = build_order_text(order, client, related_agent)
            await msg.answer(text, parse_mode="HTML")
            await msg.bot.send_message(chat_id=user_id_, text=text, parse_mode="HTML")
        except Exception as e:
            await msg.answer("Ошибка при извлечении клиента, пожалуйста, отправьте администратору: {}".format(e))
            return
        item_data = []
        default_image = FSInputFile("image/none_img.png")
        for item in order["orderProducts"]:
            u_id = str(uuid.uuid4())[:15]
            card = await Card.create(name=item['product']['name'], image=None, price=item['price'], unique_link=u_id,
                                     user=tg_user[0].id)
            item_data.append(card.unique_link)
            caption = (
                f"<b>{item['product']['name']}</b>\n"
                f"💰 Цена: <b>{item['price']}</b> сум\n"
                f"🆔 Код товара: <code>{u_id}</code>"
            )
            await msg.bot.send_photo(chat_id=user_id_, photo=default_image, caption=caption, parse_mode="HTML",
                                     reply_markup=await buy_cards_button(card.id))
        await msg.answer("✔ Все сообщения, отправленные клиенту", reply_markup=await main_menu_reply_buttons())
        return await TelegramUser.create_or_update(chat_id=str(user_id_), day=client_day, card_ids=item_data)
