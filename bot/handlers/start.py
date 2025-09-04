from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.state import any_state
from aiogram.types import Message, InlineQueryResultPhoto, InlineQuery
from aiogram.fsm.context import FSMContext

from bot.buttons.inline_buttons import main_menu_button, buy_cards_button
from bot.buttons.reply_buttons import back_user_menu_button, main_menu_reply_buttons, diller_menu_buttons
from bot.buttons.text import be_seller, back_user_menu, categories
from bot.states import StartState
from db.model import TelegramUser, Card

router = Router()

none_img_url = "AgACAgIAAxkDAAMhaJ2qou1aP_cVtpTS1J-7KVmRsDsAAj7zMRsaoOlIfuDFXr9eZBoBAAMCAANtAAM2BA"


@router.inline_query()
async def inline_search(query: InlineQuery):
    text = query.query.strip()

    if not text:
        await query.answer([], cache_time=1, is_personal=True)
        return

    items = await Card.get_by(unique_link=text)
    if not items:
        await query.answer([], cache_time=1, is_personal=True)
        return

    item = items[0]
    if item.image:
        photo_url = item.image
    else:
        photo_url = none_img_url
    results = [
        InlineQueryResultPhoto(
            id=str(item.id),
            photo_url=photo_url,
            thumbnail_url=photo_url,
            title=item.name,
            description=f"💰 {item.price} сум",
            caption=(
                f"<b>{item.name}</b>\n"
                f"💰 Цена: <b>{item.price}</b> сум\n"
                f"🆔 Код товара: <code>{item.unique_link}</code>"
            ),
            parse_mode="HTML",
            reply_markup=await buy_cards_button(item.id)
        )
    ]
    await query.answer(results, cache_time=1, is_personal=True)


@router.message(F.text.in_(['/start', back_user_menu]), StateFilter(any_state))
async def start_handler(msg: Message, state: FSMContext):
    tg_user = await TelegramUser.create_or_update(
        chat_id=str(msg.from_user.id),
        full_name=msg.from_user.full_name,
        username=msg.from_user.username,
    )
    if not tg_user.is_diller:
        await msg.answer("Добро пожаловать в наш бот", reply_markup=await main_menu_reply_buttons())
    else:
        await msg.answer("Добро пожаловать в наш бот", reply_markup=await diller_menu_buttons())
    await state.clear()


@router.message(F.text == be_seller)
async def be_seller_handler(msg: Message, state: FSMContext):
    await state.set_state(StartState.url)
    await msg.answer("Введите URL-адрес", reply_markup=await back_user_menu_button())


@router.message(StartState.url)
async def be_seller_handler_2(msg: Message, state: FSMContext):
    await state.update_data(url=msg.text)
    await state.set_state(StartState.login)
    await msg.answer("Введите ваш логин")


@router.message(StartState.login)
async def be_seller_handler_3(msg: Message, state: FSMContext):
    await state.update_data(login=msg.text)
    await state.set_state(StartState.password)
    await msg.answer("Введите пароль")


@router.message(StartState.password)
async def be_seller_handler_4(msg: Message, state: FSMContext):
    await state.update_data(password=msg.text)
    await state.set_state(StartState.type_price)
    await msg.answer("Отправить цену CS_id")


@router.message(StartState.type_price)
async def be_seller_handler_5(msg: Message, state: FSMContext):
    data = await state.get_data()
    base_url = data['url'].rstrip("/")
    final_url = f"{base_url}/api/v2/"

    await TelegramUser.create_or_update(
        chat_id=str(msg.from_user.id),
        full_name=msg.from_user.full_name,
        username=msg.from_user.username,
        url=final_url,
        login=data['login'],
        password=data['password'],
        price_type=msg.text,
        is_diller=True
    )
    buttons = await main_menu_button(url=final_url, login=data['login'], password=data['password'])
    if buttons:
        await msg.answer("Поздравляем, вы стали дилером", reply_markup=await diller_menu_buttons())
        await msg.answer("Выберите нужную категорию", reply_markup=buttons)
    else:
        await msg.answer("""
У вас нет категорий или информация неверна.

Чтобы начать заново: /start""")
    await state.clear()


@router.message(F.text == categories)
async def get_categories_handler(msg: Message):
    tg_user = await TelegramUser.get_by(chat_id=str(msg.from_user.id))
    if tg_user:
        await msg.answer("Добро пожаловать в категории",
                         reply_markup=await main_menu_button(tg_user[0].url, tg_user[0].login, tg_user[0].password))
