from aiogram import Router, types
from aiogram.filters import Command
import config
import db.db as db
import logging
from db.db import get_count

router = Router()


@router.message(Command("invite"))
async def cmd_invite(message: types.Message):
    user_id = message.from_user.id
    try:
        # Generate referral link
        bot_username = config.BOT_USERNAME
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        text = (
            "👥 Приглашай друзей и получай баллы!\n\n"
            f"🔗 Твоя ссылка: {ref_link}\n\n"
            "За каждого: +50 баллов\n"
            "Пригласи 5 — получи доступ в AI-клуб бесплатно (вместо 2500₽)"
        )
        await message.answer(text)
    except Exception as e:
        logging.exception(f"Error in cmd_invite for user {user_id}: {e}")
        await message.answer(
            "Не удалось сформировать реферальную ссылку. Попробуйте позже."
        )
        return


@router.message(Command("friends"))
async def cmd_friends(message: types.Message):
    user_id = message.from_user.id
    try:
        count = get_count("SELECT COUNT(*) FROM users WHERE invited_by = ?", (user_id,))
    except Exception as e:
        logging.exception(f"Error fetching referral count for user {user_id}: {e}")
        await message.answer(
            "Не удалось получить информацию о приглашённых. Попробуйте позже."
        )
        return
    if count == 0:
        await message.answer("🚫 Вы еще никого не пригласили.")
        return
    remaining = 5 - count
    text = (
        f"👥 *Ты пригласил:* {count} из 5\n"
        f"*Осталось:* {remaining}\n\n"
        "Каждый приглашённый = +50 баллов\n"
        "PDF-бонус выдаётся после первого!"
    )
    await message.answer(text, parse_mode="Markdown")
