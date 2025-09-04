from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, KeyboardButtonRequestUser

from bot.buttons.text import turn_off_advert, be_seller, turn_on_advert, give_permission, take_permission, \
    back_user_menu, none_advert, forward_advert, adverts, statistic, categories


async def main_menu_reply_buttons():
    design = [
        [KeyboardButton(text=turn_off_advert), KeyboardButton(text=turn_on_advert)],
        [KeyboardButton(text=be_seller)]
    ]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)


async def diller_menu_buttons():
    design = [
        [KeyboardButton(text=categories)],
    ]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)


async def admin_menu_buttons():
    design = [
        [KeyboardButton(text=adverts), KeyboardButton(text=statistic)],
        [KeyboardButton(text=give_permission), KeyboardButton(text=take_permission)],
        [KeyboardButton(text=back_user_menu)]
    ]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)


async def back_user_menu_button():
    design = [[KeyboardButton(text=back_user_menu)]]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)


def request_user_reply_keyboard(request_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👤 Выбрать пользователя",
                    request_user=KeyboardButtonRequestUser(
                        request_id=request_id
                    )
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def advert_menu_buttons():
    design = [
        [KeyboardButton(text=none_advert), KeyboardButton(text=forward_advert)],
        [KeyboardButton(text=back_user_menu)]
    ]
    return ReplyKeyboardMarkup(keyboard=design, resize_keyboard=True)
