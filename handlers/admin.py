from aiogram import Router, types
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import config
import db.db as db
from keyboards import admin_menu
import asyncio
import logging
from functools import wraps
import csv
from aiogram.types import FSInputFile
from aiogram import exceptions


def admin_only(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        user_id = (
            event.from_user.id
            if hasattr(event, "from_user")
            else event.message.from_user.id
        )
        if user_id not in config.ADMIN_IDS:
            msg = (
                "Нет доступа"
                if isinstance(event, types.CallbackQuery)
                else "⛔️ Команда доступна только администраторам."
            )
            if isinstance(event, types.CallbackQuery):
                await event.answer(msg, show_alert=True)
            else:
                await event.message.answer(msg)
            return
        return await handler(event, *args, **kwargs)

    return wrapper


def get_user_list():
    cur = db.conn.cursor()
    cur.execute("SELECT user_id, username, first_name, last_name FROM users")
    return cur.fetchall()


def parse_command_args(message: types.Message, expected_args: int):
    parts = message.text.split()
    if len(parts) != expected_args + 1:
        return None
    return parts[1:]


router = Router()


# Define FSM state for broadcast
class AdminForm(StatesGroup):
    broadcast = State()


@admin_only
@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    # Clear any admin state (in case they were in middle of broadcast)
    await state.clear()
    # Send admin menu
    await message.answer("⚙️ Админ-панель", reply_markup=admin_menu.admin_menu)


@admin_only
@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    total_users = db.get_user_count()
    premium_users = db.get_premium_count()
    referral_count = db.get_referral_count()
    # Optionally total points (sum of all user points)
    cur = db.conn.cursor()
    cur.execute("SELECT SUM(points) FROM users")
    total_points = cur.fetchone()[0] or 0
    text = (
        f"📊 Статистика:\n"
        f"Всего пользователей: {total_users}\n"
        f"Премиум пользователей: {premium_users}\n"
        f"Приглашено по рефералам: {referral_count}\n"
        f"Суммарно баллов у пользователей: {total_points}"
    )
    await callback.answer()
    await callback.message.answer(text)


@admin_only
@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    # Prompt for broadcast message
    await callback.message.answer(
        "✏️ Введите сообщение для рассылки всем пользователям:"
    )
    # Set FSM state to broadcast
    await state.set_state(AdminForm.broadcast)


@admin_only
@router.message(StateFilter(AdminForm.broadcast))
async def process_broadcast_message(message: types.Message, state: FSMContext):
    # Get all user IDs
    cur = db.conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    if not users:
        await message.answer("❗️ Нет пользователей для рассылки.")
        await state.clear()
        return
    await message.answer(f"⌛ Отправляю сообщение {len(users)} пользователям...")
    success = 0
    fail = 0
    for i, uid in enumerate(users):
        try:
            await message.copy_to(uid)
            success += 1
        except exceptions.TelegramForbiddenError:
            fail += 1
            # The user blocked the bot or left - optionally remove from DB
            db.delete_user(uid)
        except exceptions.TelegramFloodWait as e:
            # If hit flood limit, wait and continue
            await asyncio.sleep(e.retry_after)
            try:
                await message.copy_to(uid)
                success += 1
            except Exception as e:
                logging.exception(f"Failed to send broadcast to {uid}: {e}")
                fail += 1
        except Exception as e:
            logging.exception(f"Failed to send broadcast to {uid}: {e}")
            fail += 1
        # Throttle sending to avoid hitting flood limits
        if i % 20 == 19:
            await asyncio.sleep(0.5)
    await message.answer(
        f"✅ Рассылка завершена. Успешно: {success}, не доставлено: {fail}."
    )
    # Reset state
    await state.clear()


@admin_only
@router.callback_query(lambda c: c.data == "admin_show_top")
async def admin_show_top_callback(callback: types.CallbackQuery):
    await callback.answer()
    # Получаем ТОП-10 по баллам
    top = db.get_top_users(limit=10)  # [(user_id, username, first_name, points), ...]
    if not top:
        await callback.message.answer("🏆 Топ пользователей пуст.")
        return

    text = "🏆 <b>ТОП Пользователей</b>\n\n"
    for rank, (uid, uname, first, pts) in enumerate(top, start=1):
        # Гибридный способ получения количества приглашений
        user_data = db.get_user(uid)
        ref_cnt = user_data.get("referral_count") if user_data else 0
        if ref_cnt is None:
            cur = db.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users WHERE invited_by = ?", (uid,))
            ref_cnt = cur.fetchone()[0] or 0
        # Статус премиума
        premium = "✅" if user_data and user_data.get("premium") else "❌"
        # Отображение
        full_name = first or "—"
        usertag = f"@{uname}" if uname else "—"
        text += (
            f"{rank}. <code>{uid}</code> {usertag} ({full_name})\n"
            f"   • Баллы: <b>{pts}</b> | Приглашений: <b>{ref_cnt}</b> | Премиум: {premium}\n"
        )

    text += "\n🔁 Рейтинг обновляется ежемесячно."
    await callback.message.answer(text, parse_mode="HTML")


@admin_only
@router.callback_query(lambda c: c.data == "admin_reset_top")
async def admin_reset_top_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    # Reset all points to zero
    cur = db.conn.cursor()
    cur.execute("UPDATE users SET points = 0")
    db.conn.commit()
    await callback.answer("Топ успешно сброшен.", show_alert=True)
    await callback.message.answer("🏆 Таблица лидеров обнулена.")


@admin_only
@router.callback_query(lambda c: c.data == "admin_export_csv")
async def admin_export_csv_callback(callback: types.CallbackQuery):
    await callback.answer()
    # Export users data to CSV
    filename = "users_export.csv"
    cur = db.conn.cursor()
    cur.execute(
        "SELECT user_id, username, first_name, last_name, points, premium, invited_by, challenge_progress FROM users"
    )
    rows = cur.fetchall()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "user_id",
                "username",
                "first_name",
                "last_name",
                "points",
                "premium",
                "invited_by",
                "challenge_progress",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row[0],
                    row[1] or "",
                    row[2] or "",
                    row[3] or "",
                    row[4],
                    row[5],
                    row[6] or "",
                    row[7],
                ]
            )
    # Send the CSV file to admin
    doc = FSInputFile(filename, filename=filename)
    await callback.message.answer_document(
        doc, caption="📄 Экспорт данных пользователей"
    )


# List users command for admins
@admin_only
@router.message(Command("listusers"))
async def cmd_list_users(message: types.Message):
    rows = get_user_list()
    if not rows:
        await message.reply("Список пользователей пуст.")
        return
    text = "📋 Список пользователей:\n\n"
    for r in rows:
        uid = r["user_id"]
        uname = r["username"]
        first = r["first_name"] or ""
        last = r["last_name"] or ""
        if first or last:
            full_name = f"{first} {last}".strip()
        else:
            full_name = "—"
        if uname:
            display_name = f"@{uname}"
        else:
            display_name = "—"
        text += f"• <code>{uid}</code> — {display_name} ({full_name})\n"
    await message.reply(text, parse_mode="HTML")


@admin_only
@router.callback_query(lambda c: c.data and c.data.startswith("story_accept"))
async def story_accept_callback(callback: types.CallbackQuery):
    # Accept story screenshot (grant points)
    # Parse user_id from callback data
    try:
        target_id = int(callback.data.split(":")[1])
    except:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    # Check if user already submitted story
    if db.has_submitted_story(target_id):
        await callback.answer(
            "Этот пользователь уже отправлял сторис.", show_alert=True
        )
        return
    # Award points
    db.update_points(target_id, 50)
    db.mark_story_submitted(target_id)
    # Edit the original message in admin group to mark accepted
    try:
        new_caption = (callback.message.caption or "") + " ✅ Принято"
        await callback.message.edit_caption(new_caption)
    except Exception as e:
        logging.exception(f"Failed to edit caption for story_accept: {e}")
        # If cannot edit caption, remove keyboard at least
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logging.exception(f"Failed to edit caption for story_accept: {e}")
    await callback.answer("Принято ✅")
    # Notify the user in private
    try:
        await callback.message.chat.bot.send_message(
            target_id, "✅ Ваш сторис подтвержден! Вам начислено 50 баллов."
        )
    except Exception:
        pass


@admin_only
@router.callback_query(lambda c: c.data and c.data.startswith("story_reject"))
async def story_reject_callback(callback: types.CallbackQuery):
    try:
        target_id = int(callback.data.split(":")[1])
    except:
        await callback.answer("Ошибка", show_alert=True)
        return
    # Remove the inline buttons from the message (mark as processed)
    try:
        new_caption = (callback.message.caption or "") + " ❌ Отклонено"
        await callback.message.edit_caption(new_caption)
    except Exception as e:
        logging.exception(f"Failed to edit caption for story_reject: {e}")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception as e:
            logging.exception(f"Failed to edit caption for story_reject: {e}")
    await callback.answer("Отклонено")
    # Notify user about rejection
    try:
        await callback.message.chat.bot.send_message(
            target_id,
            "❌ Ваш сторис не принят. Попробуйте снова или уточните требования.",
        )
    except Exception:
        pass


@admin_only
@router.message(Command("setpremium"))
async def cmd_set_premium(message: types.Message):
    args = parse_command_args(message, 2)
    if not args or args[0].isdigit() is False or args[1] not in ("0", "1"):
        await message.bot.send_message(
            message.chat.id, "Использование: /setpremium <user_id> <0 или 1>"
        )
        return
    user_id = int(args[0])
    premium_flag = bool(int(args[1]))
    db.set_premium(user_id, premium_flag)
    await message.bot.send_message(
        message.chat.id,
        f"У пользователя {user_id} premium установлен в {int(premium_flag)}.",
    )
    # Notify affected user
    try:
        if premium_flag:
            await message.bot.send_message(user_id, "🎉 Вам выдан премиум-доступ!")
        else:
            await message.bot.send_message(user_id, "ℹ️ Ваш премиум-доступ был снят.")
    except Exception:
        pass


@admin_only
@router.message(Command("setpoints"))
async def cmd_set_points(message: types.Message):
    args = parse_command_args(message, 2)
    if not args or args[0].isdigit() is False or args[1].lstrip("-").isdigit() is False:
        await message.bot.send_message(
            message.chat.id, "Использование: /setpoints <user_id> <points>"
        )
        return
    user_id = int(args[0])
    points = int(args[1])
    db.set_points(user_id, points)
    await message.bot.send_message(
        message.chat.id,
        f"У пользователя {user_id} количество баллов установлено в {points}.",
    )
    # Notify affected user
    try:
        await message.bot.send_message(
            user_id, f"💰 Ваш баланс баллов установлен в {points}!"
        )
    except Exception:
        pass


@admin_only
@router.message(Command("ban"))
async def cmd_ban_user(message: types.Message):
    args = parse_command_args(message, 1)
    if not args or args[0].isdigit() is False:
        await message.bot.send_message(message.chat.id, "Использование: /ban <user_id>")
        return
    user_id = int(args[0])
    db.set_banned(user_id, True)
    await message.bot.send_message(
        message.chat.id, f"Пользователь {user_id} заблокирован."
    )
    # Notify affected user
    try:
        await message.bot.send_message(
            user_id, "⛔️ Вы были заблокированы администратором."
        )
    except Exception:
        pass


@admin_only
@router.message(Command("unban"))
async def cmd_unban_user(message: types.Message):
    args = parse_command_args(message, 1)
    if not args or args[0].isdigit() is False:
        await message.bot.send_message(
            message.chat.id, "Использование: /unban <user_id>"
        )
        return
    user_id = int(args[0])
    db.set_banned(user_id, False)
    await message.bot.send_message(
        message.chat.id, f"Пользователь {user_id} разблокирован."
    )
    # Notify affected user
    try:
        await message.bot.send_message(
            user_id, "✅ Вы были разблокированы администратором."
        )
    except Exception:
        pass


# New callback handlers for admin menu buttons


@admin_only
@router.callback_query(lambda c: c.data == "admin_listusers")
async def admin_listusers_callback(callback: types.CallbackQuery):
    await callback.answer()
    # Call the same logic as /listusers command
    rows = get_user_list()
    if not rows:
        await callback.message.answer("Список пользователей пуст.")
        return
    text = "📋 Список пользователей:\n\n"
    for r in rows:
        uid = r["user_id"]
        uname = r["username"]
        first = r["first_name"] or ""
        last = r["last_name"] or ""
        if first or last:
            full_name = f"{first} {last}".strip()
        else:
            full_name = "—"
        if uname:
            display_name = f"@{uname}"
        else:
            display_name = "—"
        text += f"• <code>{uid}</code> — {display_name} ({full_name})\n"
    await callback.message.answer(text, parse_mode="HTML")


@admin_only
@router.callback_query(lambda c: c.data == "admin_setpremium")
async def admin_setpremium_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/setpremium <user_id> <0 или 1>` для установки премиум статуса.",
        parse_mode="Markdown",
    )


@admin_only
@router.callback_query(lambda c: c.data == "admin_setpoints")
async def admin_setpoints_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/setpoints <user_id> <points>` для установки количества баллов.",
        parse_mode="Markdown",
    )


@admin_only
@router.callback_query(lambda c: c.data == "admin_ban")
async def admin_ban_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/ban <user_id>` для блокировки пользователя.",
        parse_mode="Markdown",
    )


# Set referrals count for a user (admin only)
@admin_only
@router.message(Command("setreferrals"))
async def cmd_set_referrals(message: types.Message):
    args = parse_command_args(message, 2)
    if not args or not args[0].isdigit() or not args[1].isdigit():
        await message.bot.send_message(
            message.chat.id, "Использование: /setreferrals <user_id> <ref_count>"
        )
        return
    user_id = int(args[0])
    ref_count = int(args[1])
    db.set_referral_count(user_id, ref_count)
    await message.bot.send_message(
        message.chat.id,
        f"Количество приглашений пользователя {user_id} установлено в {ref_count}.",
    )


# Callback handler for "Приглашения" button in admin menu
@admin_only
@router.callback_query(lambda c: c.data == "setreferrals")
async def admin_setreferrals_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/setreferrals <user_id> <ref_count>` для установки количества приглашений.",
        parse_mode="Markdown",
    )
