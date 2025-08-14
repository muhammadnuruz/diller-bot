import requests

from bot.buttons.inline_buttons import main_menu_button
from db.model import TelegramUser, Card
import os
import uuid
import tempfile
from aiogram.types import FSInputFile, CallbackQuery


async def create_cards_function(call: CallbackQuery):
    category_id = call.data[9:]
    tg_user = await TelegramUser.get_by(chat_id=str(call.from_user.id))

    login_data = {
        "method": "login",
        "auth": {
            "login": tg_user[0].login,
            "password": tg_user[0].password
        }
    }

    res = requests.get(tg_user[0].url, json=login_data).json()
    if not res.get("status"):
        await call.message.answer("Ошибка авторизации. Попробуйте /start")
        return

    token = res["result"]["token"]
    user_id = res["result"]["userId"]

    items = []
    for i in range(4):
        data = {
            "method": "getProduct",
            "auth": {"userId": user_id, "token": token},
            "params": {"page": i + 1, "limit": 1000}
        }
        data_res = requests.get(tg_user[0].url, json=data).json()
        items.extend(data_res["result"].get("product", []))

    prices = await get_prices(tg_user[0].url, user_id, token, tg_user[0].price_type)
    default_image = FSInputFile("image/none_img.png")

    for item in items:
        if item['category']['CS_id'] != category_id or item['active'] != "Y":
            continue

        cs_id = item.get("CS_id")
        name = item.get("name", "").strip()
        imageUrl = item.get("imageUrl") or None
        price = prices.get(cs_id, 0)
        u_id = str(uuid.uuid4())[:15]

        caption = (
            f"<b>{name}</b>\n"
            f"💰 Цена: <b>{price}</b> сум\n"
            f"🆔 Код товара: <code>{u_id}</code>"
        )

        await Card.create(name=name, image=tg_user[0].url[:-7] + imageUrl, price=price, unique_link=u_id,
                          user=tg_user[0].id)

        if imageUrl:
            photo_url = tg_user[0].url[:-7] + imageUrl
            try:
                resp = requests.get(photo_url)
                if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                    tmp_file.write(resp.content)
                    tmp_file.close()
                    await call.message.answer_photo(FSInputFile(tmp_file.name), caption=caption, parse_mode="HTML")
                    os.remove(tmp_file.name)
                    continue
            except:
                pass

        await call.message.answer_photo(default_image, caption=caption, parse_mode="HTML")

    buttons = await main_menu_button(url=tg_user[0].url, login=tg_user[0].login, password=tg_user[0].password)
    if buttons:
        await call.message.answer(text="Выберите нужную категорию", reply_markup=buttons)
    else:
        await call.message.answer("""
У вас нет категорий или информация неверна.

Чтобы начать заново: /start
""")


async def get_prices(url, user_id, token, price_type):
    response = requests.get(
        url,
        json={
            "auth": {
                "userId": user_id,
                "token": token
            },
            "method": "getPrice",
            "params": {
                "priceType": {
                    "SD_id": price_type,
                }
            }
        }
    )
    result = response.json()
    if result['status'] is True:
        lst = result['result']
        prices = {price['product']["CS_id"]: price["price"] for price in lst}
        return prices
    return []
