from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.buttons.text import plus_1, plus_5, plus_10, clear_basket, close_order, forward_to_bot, my_orders, \
    send_new_order
from db.model import TelegramUser

USERS_PER_PAGE = 10


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


async def new_order_button(id_):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=send_new_order, callback_data="send:new:order:{}".format(id_))]
    ])


async def give_permission_button(page: int = 1):
    telegram_users = await TelegramUser.get_by(is_purchase=False, is_diller=True)

    start = (page - 1) * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    users_page = telegram_users[start:end]

    kb = InlineKeyboardBuilder()

    for user in users_page:
        full_name = user.full_name or "—"
        username = f"@{user.username}" if user.username else ""
        text = f"{full_name} {username}"
        kb.row(
            InlineKeyboardButton(
                text=text.strip(),
                callback_data=f"give_perm_{user.chat_id}"
            )
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"users_page:{page - 1}")
        )
    if end < len(telegram_users):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"users_page:{page + 1}")
        )

    if nav_buttons:
        kb.row(*nav_buttons)

    return kb.as_markup()


async def take_permission_button(page: int = 1):
    telegram_users = await TelegramUser.get_by(is_purchase=True)
    start = (page - 1) * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    users_page = telegram_users[start:end]

    kb = InlineKeyboardBuilder()

    for user in users_page:
        full_name = user.full_name or "—"
        username = f"@{user.username}" if user.username else ""
        text = f"{full_name} {username}"
        kb.row(
            InlineKeyboardButton(
                text=text.strip(),
                callback_data=f"take_perm_{user.chat_id}"
            )
        )

    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"users_page:{page - 1}")
        )
    if end < len(telegram_users):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"users_page:{page + 1}")
        )

    if nav_buttons:
        kb.row(*nav_buttons)

    return kb.as_markup()
