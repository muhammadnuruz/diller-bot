from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.buttons.inline_buttons import give_permission_button, take_permission_button
from bot.buttons.reply_buttons import admin_menu_buttons
from bot.buttons.text import give_permission, take_permission
from db.model import TelegramUser

admins = [1974800905, 999090234]

router = Router()


@router.message(F.text == "/admin")
async def admin_menu_handler(msg: Message):
    if msg.from_user.id not in admins:
        return
    await msg.answer(text="Добро пожаловать в меню администратора", reply_markup=await admin_menu_buttons())


@router.message(F.text == give_permission)
async def give_permission_handler(msg: Message):
    await msg.answer(text="Выберите пользователя, которому необходимо предоставить разрешение 🔽",
                     reply_markup=await give_permission_button())


@router.callback_query(F.data.startswith("give_perm_"))
async def give_permission_handler_2(call: CallbackQuery):
    _, __, id_ = call.data.split("_")
    await TelegramUser.create_or_update(chat_id=id_, is_purchase=True, purchase_data=datetime.now())
    await call.message.delete()
    await call.message.answer(text="Разрешение предоставлено ✔")


@router.message(F.text == take_permission)
async def give_permission_handler(msg: Message):
    await msg.answer(text="Выберите пользователя, разрешение которого вы хотите удалить 🔽",
                     reply_markup=await take_permission_button())


@router.callback_query(F.data.startswith("take_perm_"))
async def take_permission_handler_2(call: CallbackQuery):
    _, __, id_ = call.data.split("_")
    await TelegramUser.create_or_update(chat_id=id_, is_purchase=False)
    await call.message.delete()
    await call.message.answer(text="Разрешение удалено ✔")
