from aiogram import Router, types
from aiogram.filters import Command
import config
import db.db as db

router = Router()


@router.message(Command("invite"))
async def cmd_invite(message: types.Message):
    user_id = message.from_user.id
    # Generate referral link with user's id
    bot_username = config.BOT_USERNAME
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    # text for inviting friends (ref_link inserted appropriately)
    text = (
        "👥 Приглашай друзей и получай баллы!\n\n"
        f"🔗 Твоя ссылка: {ref_link}\n\n"
        "За каждого: +50 баллов\n"
        "Пригласи 5 — получи доступ в AI-клуб бесплатно (вместо 2500₽)"
    )
    await message.answer(text)


@router.message(Command("friends"))
async def cmd_friends(message: types.Message):
    user_id = message.from_user.id
    cur = db.conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE invited_by = ?",
        (user_id,),
    )
    row = cur.fetchone()
    count = row[0] if row else 0
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
