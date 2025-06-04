from aiogram import Router, types
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import config
import db.db as db
from keyboards import admin_menu
import asyncio
from aiogram import exceptions


router = Router()


# Define FSM state for broadcast
class AdminForm(StatesGroup):
    broadcast = State()


@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔️ Команда доступна только администраторам.")
        return
    # Clear any admin state (in case they were in middle of broadcast)
    await state.clear()
    # Send admin menu
    await message.answer("⚙️ Админ-панель", reply_markup=admin_menu.admin_menu)


@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
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


@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    # Prompt for broadcast message
    await callback.message.answer(
        "✏️ Введите сообщение для рассылки всем пользователям:"
    )
    # Set FSM state to broadcast
    await state.set_state(AdminForm.broadcast)


@router.message(StateFilter(AdminForm.broadcast))
async def process_broadcast_message(message: types.Message, state: FSMContext):
    # Only admins should reach here, but double-check
    if message.from_user.id not in config.ADMIN_IDS:
        return
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
            except Exception:
                fail += 1
        except Exception:
            fail += 1
        # Throttle sending to avoid hitting flood limits
        if i % 20 == 0:
            await asyncio.sleep(0.5)
    await message.answer(
        f"✅ Рассылка завершена. Успешно: {success}, не доставлено: {fail}."
    )
    # Reset state
    await state.clear()


@router.callback_query(lambda c: c.data == "admin_send_pdf")
async def admin_send_pdf_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    # Get all user IDs
    cur = db.conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = [row[0] for row in cur.fetchall()]
    if not users:
        await callback.message.answer("Нет пользователей для отправки PDF.")
        return
    await callback.message.answer(
        f"⌛ Отправка PDF файла {len(users)} пользователям..."
    )
    success = 0
    fail = 0
    from aiogram.types import FSInputFile

    doc = FSInputFile("gift.pdf")
    for i, uid in enumerate(users):
        try:
            await callback.message.chat.bot.send_document(uid, doc)
            success += 1
        except exceptions.TelegramForbiddenError:
            fail += 1
            db.delete_user(uid)
        except exceptions.TelegramFloodWait as e:
            await asyncio.sleep(e.retry_after)
            try:
                await callback.message.chat.bot.send_document(uid, doc)
                success += 1
            except Exception:
                fail += 1
        except Exception:
            fail += 1
        if i % 10 == 0:
            await asyncio.sleep(1)
    await callback.message.answer(
        f"✅ PDF отправлен. Успешно: {success}, не удалось: {fail}."
    )


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


@router.callback_query(lambda c: c.data == "admin_export_csv")
async def admin_export_csv_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    # Export users data to CSV
    import csv

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
    from aiogram.types import FSInputFile

    doc = FSInputFile(filename, filename=filename)
    await callback.message.answer_document(
        doc, caption="📄 Экспорт данных пользователей"
    )


# List users command for admins
@router.message(Command("listusers"))
async def cmd_list_users(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        return
    cur = db.conn.cursor()
    cur.execute("SELECT user_id, username, first_name, last_name FROM users")
    rows = cur.fetchall()
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
        text += f"• `{uid}` — {display_name} ({full_name})\n"
    await message.reply(text, parse_mode="Markdown")


@router.callback_query(lambda c: c.data and c.data.startswith("story_accept"))
async def story_accept_callback(callback: types.CallbackQuery):
    # Accept story screenshot (grant points)
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
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
    except:
        # If cannot edit caption, remove keyboard at least
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass
    await callback.answer("Принято ✅")
    # Notify the user in private
    try:
        await callback.message.chat.bot.send_message(
            target_id, "✅ Ваш сторис подтвержден! Вам начислено 50 баллов."
        )
    except:
        pass


@router.callback_query(lambda c: c.data and c.data.startswith("story_reject"))
async def story_reject_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    try:
        target_id = int(callback.data.split(":")[1])
    except:
        await callback.answer("Ошибка", show_alert=True)
        return
    # Remove the inline buttons from the message (mark as processed)
    try:
        new_caption = (callback.message.caption or "") + " ❌ Отклонено"
        await callback.message.edit_caption(new_caption)
    except:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass
    await callback.answer("Отклонено")
    # Notify user about rejection
    try:
        await callback.message.chat.bot.send_message(
            target_id,
            "❌ Ваш сторис не принят. Попробуйте снова или уточните требования.",
        )
    except:
        pass


@router.message(Command("setpremium"))
async def cmd_set_premium(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.bot.send_message(message.chat.id, "Нет доступа")
        return
    parts = message.text.split()
    if len(parts) != 3 or parts[1].isdigit() is False or parts[2] not in ("0", "1"):
        await message.bot.send_message(
            message.chat.id, "Использование: /setpremium <user_id> <0 или 1>"
        )
        return
    user_id = int(parts[1])
    premium_flag = bool(int(parts[2]))
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


@router.message(Command("setpoints"))
async def cmd_set_points(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.bot.send_message(message.chat.id, "Нет доступа")
        return
    parts = message.text.split()
    if (
        len(parts) != 3
        or parts[1].isdigit() is False
        or parts[2].lstrip("-").isdigit() is False
    ):
        await message.bot.send_message(
            message.chat.id, "Использование: /setpoints <user_id> <points>"
        )
        return
    user_id = int(parts[1])
    points = int(parts[2])
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


@router.message(Command("ban"))
async def cmd_ban_user(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.bot.send_message(message.chat.id, "Нет доступа")
        return
    parts = message.text.split()
    if len(parts) != 2 or parts[1].isdigit() is False:
        await message.bot.send_message(message.chat.id, "Использование: /ban <user_id>")
        return
    user_id = int(parts[1])
    db.ban_user(user_id)
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


@router.message(Command("unban"))
async def cmd_unban_user(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.bot.send_message(message.chat.id, "Нет доступа")
        return
    parts = message.text.split()
    if len(parts) != 2 or parts[1].isdigit() is False:
        await message.bot.send_message(
            message.chat.id, "Использование: /unban <user_id>"
        )
        return
    user_id = int(parts[1])
    db.unban_user(user_id)
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


@router.callback_query(lambda c: c.data == "admin_listusers")
async def admin_listusers_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    # Call the same logic as /listusers command
    cur = db.conn.cursor()
    cur.execute("SELECT user_id, username, first_name, last_name FROM users")
    rows = cur.fetchall()
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
        text += f"• `{uid}` — {display_name} ({full_name})\n"
    await callback.message.answer(text, parse_mode="Markdown")


@router.callback_query(lambda c: c.data == "admin_setpremium")
async def admin_setpremium_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/setpremium <user_id> <0 или 1>` для установки премиум статуса.",
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "admin_setpoints")
async def admin_setpoints_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/setpoints <user_id> <points>` для установки количества баллов.",
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "admin_ban")
async def admin_ban_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/ban <user_id>` для блокировки пользователя.",
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "admin_unban")
async def admin_unban_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "Используйте команду `/unban <user_id>` для разблокировки пользователя.",
        parse_mode="Markdown",
    )
