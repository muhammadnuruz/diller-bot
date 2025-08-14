from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

from bot.buttons.text import plus_1, plus_5, plus_10, clear_basket, close_order, forward_to_bot, my_orders


async def main_menu_button(url, login, password):
    design = []
    login_data = {
        "method": "login",
        "auth": {
            "login": login,
            "password": password
        }
    }
    try:
        res = requests.get(url, json=login_data).json()
        if res.get("status"):
            token = res["result"]["token"]
            user_id = res["result"]["userId"]

            category_data = {
                "method": "getProductCategory",
                "auth": {"userId": user_id, "token": token}
            }
            res = requests.get(url, json=category_data).json()
            for category in res['result']['productCategory']:
                if category['active'] == "Y":
                    design.append([
                        InlineKeyboardButton(
                            text=category['name'],
                            callback_data=f"category_{category['CS_id']}"
                        )
                    ])
            if len(design) == 0:
                return None
            design.append([InlineKeyboardButton(text=my_orders, callback_data=my_orders)])
            return InlineKeyboardMarkup(inline_keyboard=design)

        return None
    except Exception:
        return None


async def buy_cards_button(id_: int):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=plus_1, callback_data=f"plus_1_{id_}"),
            InlineKeyboardButton(text=plus_5, callback_data=f"plus_5_{id_}"),
            InlineKeyboardButton(text=plus_10, callback_data=f"plus_10_{id_}")
        ],
        [
            InlineKeyboardButton(text=clear_basket, callback_data=f"clear_basket_{id_}"),
            InlineKeyboardButton(text=close_order, callback_data=f"close_order_{id_}")
        ],
        [
            InlineKeyboardButton(text=forward_to_bot, url="https://t.me/TujjorsBot")
        ]
    ])
    return markup
