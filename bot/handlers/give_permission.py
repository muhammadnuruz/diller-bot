from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.buttons.inline_buttons import give_permission_button, take_permission_button
from bot.buttons.reply_buttons import admin_menu_buttons
from bot.buttons.text import give_permission, take_permission
from bot.states import PermissionState
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
async def give_permission_handler_2(call: CallbackQuery, state: FSMContext):
    _, __, id_ = call.data.split("_")
    await state.update_data(user_id=id_)
    await call.message.delete()
    await call.message.answer("⏳ На сколько дней дать разрешение?")
    await state.set_state(PermissionState.waiting_for_days)


@router.message(PermissionState.waiting_for_days)
async def set_permission_days(msg: Message, state: FSMContext):
    try:
        days = int(msg.text)
        data = await state.get_data()
        user_id = data["user_id"]
        expire_date = datetime.now() + timedelta(days=days)
        await TelegramUser.create_or_update(
            chat_id=user_id,
            is_purchase=True,
            purchase_data=expire_date
        )
        await msg.answer(f"✔ Разрешение предоставлено на {days} дней (до {expire_date.date()})")
    except ValueError:
        await msg.answer("❌ Пожалуйста, введите число (количество дней).")
        return

    await state.clear()


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
