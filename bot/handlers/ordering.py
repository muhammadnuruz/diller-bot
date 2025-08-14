from aiogram.types import CallbackQuery
from aiogram import Router, F

from db.model import Card, Basket, TelegramUser, Order

router = Router()


@router.callback_query(F.data.startswith("plus_"))
async def ordering_function(call: CallbackQuery):
    _, num, id_ = call.data.split("_")
    card = await Card.get_by(id=int(id_))
    basket = await Basket.create_or_update_basket(
        card=int(card[0].id),
        chat_id=str(call.from_user.id),
        count=int(num),
        shop=card[0].user,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
    )
    total_price = await Basket.get_total_price(card[0].user, user_id=str(call.from_user.id), CardModel=Card)
    await call.answer(
        f"🧺 {num} товаров добавлено в корзину.\n"
        f"💰 Общая стоимость: {total_price:,}".replace(",", " ") + " сум\n"
                                                                  f"📦 Всего в корзине: {basket.count} товаров.",
        show_alert=True
    )


def format_order_message(order) -> str:
    lines = ["🆕 Новый заказ!\n"]

    lines.append("👤 Клиент:")
    lines.append(f"📛 Имя: {order.full_name or '—'}")
    lines.append(f'📎 Профиль:<a href="tg://user?id={order.chat_id}">{order.chat_id}</a>')

    if order.username:
        lines.append(f"🔗 Чат: @{order.username}")

    lines.append("")

    lines.append("📦 Товары:")
    for idx, item in enumerate(order.cards, start=1):
        total_price = item['count'] * item['price']
        lines.append(
            f"{idx}. {item['name']} — {item['count']} шт. × {item['price']:,}".replace(",", " ") +
            f" сум = {total_price:,}".replace(",", " ") + " сум"
        )
    lines.append(f"\n💰 Общая сумма: {order.total_sum:,}".replace(",", " ") + " сум")

    lines.append(f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}")

    return "\n".join(lines)


@router.callback_query(F.data.startswith("close_order_"))
async def ordering_function_2(call: CallbackQuery):
    id_ = call.data.split("_")[-1]
    card = await Card.get_by(id=int(id_))
    if not card:
        await call.answer("⛔ Карточка не найдена.", show_alert=True)
        return

    shop = await TelegramUser.get_by(id=card[0].user)
    order = await Order.create_order(str(call.from_user.id), shop[0].id, Basket, Order, Card, call.from_user.full_name,
                                     call.from_user.username)

    if not order:
        await call.answer("⛔ Ваша корзина пуста.", show_alert=True)
        return

    text = format_order_message(order)

    await call.answer(text=f"✅ Ваш заказ успешно оформлен!", show_alert=True)

    try:
        await call.bot.send_message(chat_id=shop[0].chat_id, text=f"{text}", parse_mode="HTML")
    except Exception:
        pass


@router.callback_query(F.data.startswith("clear_basket_"))
async def clear_basket_function(call: CallbackQuery):
    await Basket.delete(str(call.from_user.id))
    await call.answer("🗑 Корзина успешно очищена!", show_alert=True)
