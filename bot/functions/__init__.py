import logging
import re

from bot.buttons.inline_buttons import new_order_button
from bot.dispatcher import bot
from bot.functions.new_orders import main_function

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    if not phone:
        return "—"

    digits = re.sub(r"\D", "", phone)

    if digits.startswith("998"):
        digits = "+" + digits
    elif digits.startswith("8") and len(digits) == 9:
        digits = "+998" + digits[1:]
    elif len(digits) == 9:
        digits = "+998" + digits
    elif not digits.startswith("+"):
        digits = "+" + digits

    if len(digits) < 12:
        return "—"

    return digits


def build_order_text(order, related_user, related_agent):
    phone = normalize_phone(related_user.get("tel"))
    lines = [
        f"📦 <b>Заказ ID:</b> <code>{order.get('CS_id', '—')}</code>",
        f"📅 <b>Дата:</b> {order.get('dateCreate', '—')}",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"👤 <b>Клиент:</b> {related_user.get('name', '—')}",
        f"🆔 <b>CS_id:</b> <code>{related_user.get('CS_id', '—')}</code>",
        f"📱 <b>Телефон:</b> {phone}",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"🆔 <b>CS_id:</b> <code>{related_agent.get('CS_id', '—')}</code>",
        f"🧑‍💼 <b>Агент:</b> {related_agent.get('name', '—')}",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "🛒 <b>Товары:</b>"
    ]

    if order.get("orderProducts"):
        for idx, p in enumerate(order["orderProducts"], start=1):
            product_name = p["product"].get("name", "—")
            quantity = p.get("quantity", 0)
            summa = f"{p.get('summa', 0):,}".replace(",", " ")
            lines.append(f"{idx}. {product_name} × {quantity} = <b>{summa}</b>")
    else:
        lines.append("— Нет товаров —")

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 <b>Итого:</b> <b>{order.get('totalSummaAfterDiscount', 0)}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━",
    ])
    return "\n".join(lines)


async def run_main_function():
    try:
        datas = await main_function()
        for data in datas:
            try:
                user = data["user"]
                orders = data.get("orders", {})
                agents = data.get("agents", {}).get("result", {}).get("agent", [])
                clients = data.get("clients", [])

                for order, client in zip(orders.get("result", {}).get("order", []), clients):
                    try:
                        related_agent = {
                            "CS_id": order.get("agent", {}).get("CS_id", "—"),
                            "name": "Информация об агенте не найдена"
                        }
                        related_user = {
                            "CS_id": order.get("client", {}).get("CS_id", "—"),
                            "name": order.get("client", {}).get("clientName", "—"),
                            "tel": "Информация о клиенте не найдена"
                        }

                        for agent in agents:
                            if agent.get("CS_id") == order.get("agent", {}).get("CS_id"):
                                related_agent = {
                                    "CS_id": agent.get("CS_id", "—"),
                                    "name": agent.get("name", "—")
                                }

                        for new_client in client.get("result", {}).get("client", []):
                            if new_client.get("CS_id") == order.get("client", {}).get("CS_id"):
                                related_user = {
                                    "CS_id": new_client.get("CS_id", "—"),
                                    "name": new_client.get("name", "—"),
                                    "tel": new_client.get("tel", "—")
                                }

                        text = build_order_text(order, related_user, related_agent)

                        try:
                            await bot.send_message(user.chat_id, text, parse_mode="HTML",
                                                   reply_markup=await new_order_button(order["CS_id"]))
                        except Exception as e:
                            logger.warning(f"⚠️ Xatolik: foydalanuvchiga {user.chat_id} yuborilmadi: {e}")

                    except Exception as e:
                        logger.exception(
                            f"❌ Xatolik: foydalanuvchi {data['user'].chat_id} uchun orderni qayta ishlashda: {e}")

            except Exception as e:
                logger.exception(f"❌ Xatolik: foydalanuvchi {data.get('user')} ma’lumotlarini qayta ishlashda: {e}")

    except Exception as e:
        logger.exception(f"❌ Umumiy background xatolik: {e}")
