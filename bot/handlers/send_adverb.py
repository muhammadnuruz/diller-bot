import asyncio
import logging
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy.ext.asyncio import AsyncSession

from bot.buttons.reply_buttons import main_menu_reply_buttons, back_user_menu_button, advert_menu_buttons
from bot.buttons.text import adverts, none_advert, forward_advert, statistic, back_user_menu
from bot.handlers.give_permission import admins
from bot.states import AdverbState
from db.model import TelegramUser

router = Router()
logger = logging.getLogger(__name__)

active_broadcasts = {}


async def get_all_users():
    return await TelegramUser.get_by()


def get_cancel_keyboard(broadcast_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=back_user_menu, callback_data=f"cancel_broadcast_{broadcast_id}")]
    ])


async def broadcast_loop(
        users,
        broadcast_id: str,
        send_func,
        progress_msg: types.Message,
        progress_template: str,
        final_template: str
):
    success_count = failed_count = blocked_count = 0

    try:
        for i, user in enumerate(users):
            if not active_broadcasts.get(broadcast_id, False):
                await progress_msg.edit_text(
                    "❌ Рассылка отменена администратором\n\n"
                    f"📊 Статистика до отмены:\n"
                    f"📩 Успешно: {success_count}\n"
                    f"🚫 Заблокировали: {blocked_count}\n"
                    f"⚠️ Ошибки: {failed_count}\n"
                    f"👥 Обработано: {i}/{len(users)}"
                )
                return success_count, failed_count, blocked_count

            try:
                await send_func(user)
                success_count += 1

            except TelegramForbiddenError:
                blocked_count += 1
                logger.info(f"User {user.chat_id} has blocked the bot")

            except TelegramBadRequest as e:
                failed_count += 1
                logger.warning(f"Bad request to {user.chat_id}: {e}")

            except TelegramRetryAfter as e:
                logger.warning(f"Rate limit hit, waiting {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                try:
                    await send_func(user)
                    success_count += 1
                except Exception as e2:
                    failed_count += 1
                    logger.error(f"Retry failed for {user.chat_id}: {e2}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Unexpected error sending to {user.chat_id}", exc_info=True)

            if (i + 1) % 50 == 0 or i == len(users) - 1:
                try:
                    await progress_msg.edit_text(
                        progress_template.format(
                            total=len(users),
                            done=i + 1,
                            success=success_count,
                            blocked=blocked_count,
                            failed=failed_count
                        ),
                        reply_markup=get_cancel_keyboard(broadcast_id)
                    )
                except:
                    pass

            await asyncio.sleep(0.02)
            if (i + 1) % 200 == 0:
                await asyncio.sleep(1)

    finally:
        active_broadcasts.pop(broadcast_id, None)

    success_rate = round((success_count / len(users)) * 100, 1) if users else 0

    try:
        await progress_msg.edit_text(
            final_template.format(
                success=success_count,
                blocked=blocked_count,
                failed=failed_count,
                total=len(users),
                rate=success_rate
            )
        )
    except:
        pass

    return success_count, failed_count, blocked_count


@router.message(F.text == adverts)
async def advert_handler(msg: types.Message):
    if msg.from_user.id in admins:
        await msg.answer(
            "Какое сообщение хотите отправить ❓",
            reply_markup=await advert_menu_buttons()
        )


@router.message(F.text == none_advert)
async def none_advert_handler(msg: types.Message, state: FSMContext):
    if msg.from_user.id in admins:
        await state.set_state(AdverbState.none_adverb)
        await msg.answer(
            "Отправьте ваше сообщение ❗\n"
            "🎯 Поддерживаются все типы контента:\n"
            "• Текст, фото, видео\n"
            "• Документы, аудио, голосовые\n"
            "• Стикеры, анимации, опросы\n"
            "• Контакты, геолокация и др.",
            reply_markup=await back_user_menu_button()
        )


@router.message(AdverbState.none_adverb)
async def send_advert_to_users(msg: types.Message, state: FSMContext):
    await state.clear()

    users = await get_all_users()
    if not users:
        await msg.answer("❌ Пользователи не найдены!", reply_markup=await main_menu_reply_buttons())
        return

    broadcast_id = f"copy_{msg.from_user.id}_{msg.message_id}"
    active_broadcasts[broadcast_id] = True

    progress_msg = await msg.answer(
        f"✅ Начата рассылка!\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"📊 Прогресс: 0/{len(users)}",
        reply_markup=get_cancel_keyboard(broadcast_id)
    )

    async def send_func(user):
        await msg.copy_to(chat_id=int(user.chat_id))

    progress_template = (
        "⏳ Идет рассылка...\n"
        "👥 Всего: {total}\n"
        "📊 Прогресс: {done}/{total}\n"
        "✅ Доставлено: {success}\n"
        "🚫 Заблокировали: {blocked}\n"
        "❌ Ошибки: {failed}"
    )

    final_template = (
        "✅ Рассылка завершена\n\n"
        "📊 Подробная статистика:\n"
        "📩 Доставлено: {success}\n"
        "🚫 Заблокировали: {blocked}\n"
        "⚠️ Ошибки: {failed}\n"
        "👥 Всего: {total}\n"
        "📈 Успешность: {rate}%"
    )

    await broadcast_loop(users, broadcast_id, send_func, progress_msg, progress_template, final_template)

    await msg.answer("🏠 Возвращаемся в главное меню", reply_markup=await main_menu_reply_buttons())


@router.message(F.text == forward_advert)
async def forward_advert_handler(msg: types.Message, state: FSMContext):
    if msg.from_user.id in admins:
        await state.set_state(AdverbState.forward_adverb)
        await msg.answer(
            "📨 Отправьте сообщение для пересылки\n"
            "🔄 Поддерживаются ВСЕ типы контента:\n"
            "• Любые сообщения будут переданы как есть\n"
            "• Сохранится оригинальное форматирование\n"
            "• Включая служебные сообщения",
            reply_markup=await back_user_menu_button()
        )


@router.message(AdverbState.forward_adverb)
async def send_forward_to_users(msg: types.Message, state: FSMContext, bot: Bot):
    await state.clear()

    users = await get_all_users()
    if not users:
        await msg.answer("❌ Пользователи не найдены!", reply_markup=await main_menu_reply_buttons())
        return

    broadcast_id = f"forward_{msg.from_user.id}_{msg.message_id}"
    active_broadcasts[broadcast_id] = True

    progress_msg = await msg.answer(
        f"✅ Начата пересылка!\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"📊 Прогресс: 0/{len(users)}",
        reply_markup=get_cancel_keyboard(broadcast_id)
    )

    async def send_func(user):
        await bot.forward_message(chat_id=int(user.chat_id), from_chat_id=msg.chat.id, message_id=msg.message_id)

    progress_template = (
        "⏳ Идет пересылка...\n"
        "👥 Всего: {total}\n"
        "📊 Прогресс: {done}/{total}\n"
        "✅ Переслано: {success}\n"
        "🚫 Заблокировали: {blocked}\n"
        "❌ Ошибки: {failed}"
    )

    final_template = (
        "📢 Пересылка завершена\n\n"
        "📊 Подробная статистика:\n"
        "📩 Переслано: {success}\n"
        "🚫 Заблокировали: {blocked}\n"
        "⚠️ Ошибки: {failed}\n"
        "👥 Всего: {total}\n"
        "📈 Успешность: {rate}%"
    )

    await broadcast_loop(users, broadcast_id, send_func, progress_msg, progress_template, final_template)

    await msg.answer("🏠 Возвращаемся в главное меню", reply_markup=await main_menu_reply_buttons())


@router.callback_query(F.data.startswith("cancel_broadcast_"))
async def cancel_broadcast_handler(callback: types.CallbackQuery):
    if callback.from_user.id not in admins:
        return

    broadcast_id = callback.data.replace("cancel_broadcast_", "")
    if broadcast_id in active_broadcasts:
        active_broadcasts[broadcast_id] = False
        await callback.answer("✅ Рассылка будет остановлена")
    else:
        await callback.answer("ℹ️ Рассылка уже завершена")


@router.message(F.text == statistic)
async def stats_handler(msg: types.Message):
    if msg.from_user.id not in admins:
        return

    users = await get_all_users()
    total_users = len(users)
    active_count = len([k for k, v in active_broadcasts.items() if v])

    stats_text = f"📊 Статистика бота\n\n"
    stats_text += f"👥 Всего пользователей: {total_users:,}\n"
    stats_text += f"🔄 Активных рассылок: {active_count}\n"
    stats_text += f"📅 Обновлено: {msg.date.strftime('%d.%m.%Y %H:%M')}"

    await msg.answer(stats_text)
