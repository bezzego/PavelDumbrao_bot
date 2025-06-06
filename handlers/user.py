import sqlite3
import random
import string
from aiogram.enums import ParseMode
from aiogram import Router, types
from aiogram.types import InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import FSInputFile
import asyncio
import datetime
import calendar
import db.db as db
import config
from config import CLOSED_CHAT_URL
from keyboards import user_menu, admin_menu
from utils.misc import check_subscription
from handlers import lessons, referral, premium

# Import payment utils
from utils.yoomoney import generate_payment_label, create_payment_url

# --- Promo context for tariff promo codes ---
promo_context = {}  # user_id -> tariff_key

router = Router()


@router.message(lambda m: m.text and m.text.upper().startswith("GPT"))
async def handle_promo_code(message: types.Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    code = message.text.upper()
    discounted_amount = None
    discount_percent = None
    label = None
    button_text = None
    # --- Determine tariff_key from promo_context, fallback to default ---
    global TARIFFS
    tariff_key = promo_context.get(user_id, "tariff_1")
    base_amount = TARIFFS.get(tariff_key, 2490)

    # First, check for a TOP2/TOP3 promo code in the DB
    promo_record = db.get_promo(code)
    if promo_record:
        if promo_record["used"]:
            await message.answer("Этот промокод уже использован.")
            promo_context.pop(user_id, None)
            return
        if promo_record["user_id"] != user_id:
            await message.answer("Этот промокод не принадлежит вам.")
            promo_context.pop(user_id, None)
            return
        # Determine discount percent based on promo type
        if promo_record["type"] in ("TOP2", "TOP3"):
            db.set_premium(user_id, 2 if promo_record["type"] == "TOP2" else 3)
            discount_percent = 30
        else:
            await message.answer("Неверный тип промокода.")
            promo_context.pop(user_id, None)
            return
        discounted_amount = int(base_amount * (100 - discount_percent) / 100)
        button_text = f"Оплатить со скидкой {discounted_amount} ₽"
        label = generate_payment_label(user_id)
        db.add_payment(label, user_id, discounted_amount)
        url = await create_payment_url(discounted_amount, label)
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=button_text,
                        url=url,
                    )
                ]
            ]
        )
        await message.answer(
            f"Ваш промокод применён! Ваша скидка {discount_percent}% активирована.\n\n"
            f"Для оплаты доступа по сниженной цене нажмите кнопку ниже:",
            reply_markup=kb,
        )
        db.mark_promo_used(code)
        promo_context.pop(user_id, None)
        return
    # Fallback to GPTDISCOUNT 10% code
    if code == "GPTDISCOUNT":
        db.set_premium(user_id, 2)
        discounted_amount = int(base_amount * 0.9)
        discount_percent = 10
        button_text = f"Оплатить со скидкой {discounted_amount} ₽"
        label = generate_payment_label(user_id)
        db.add_payment(label, user_id, discounted_amount)
        url = await create_payment_url(discounted_amount, label)
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=button_text,
                        url=url,
                    )
                ]
            ]
        )
        await message.answer(
            f"Ваш промокод применён! Ваша скидка {discount_percent}% активирована.\n\n"
            f"Для оплаты доступа по сниженной цене нажмите кнопку ниже:",
            reply_markup=kb,
        )
        promo_context.pop(user_id, None)
        return
    else:
        await message.answer("Неверный промокод.")
        promo_context.pop(user_id, None)
        return


@router.message(lambda m: m.photo)
async def handle_screenshot(message: types.Message):
    """Handle user sending a screenshot of story."""
    user = message.from_user
    user_id = user.id
    # Forward (actually copy) the photo to the review group with inline buttons
    caption = f"От "
    if user.username:
        caption += f"@{user.username}"
    else:
        caption += f"<a href=\"tg://user?id={user_id}\">{user.first_name or 'пользователя'}</a>"
    caption += ": скриншот сторис"
    markup = admin_menu.story_review_keyboard(user_id)
    # Use HTML parse mode for mention link
    try:
        await message.copy_to(
            config.GROUP_ID, caption=caption, reply_markup=markup, parse_mode="HTML"
        )
    except Exception as e:
        # If sending to group fails, notify user
        await message.answer(
            "Ошибка при отправке скриншота на проверку. Попробуйте позже."
        )
        return
    # Confirm to user
    await message.answer("📷 Ваш скриншот отправлен на проверку модератору.")
    await message.answer("Выберите действие:", reply_markup=user_menu.main_menu)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user = message.from_user
    user_id = user.id
    # Parse referral parameter if any (after /start)
    args = message.text.split()
    referral_id = None
    if len(args) > 1:
        referral_arg = args[1]
        if referral_arg.isdigit():
            ref_id_int = int(referral_arg)
            if ref_id_int != user_id:
                referral_id = ref_id_int

    # Add user to DB (if not already)
    new_user = db.add_user(
        user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        invited_by=referral_id,
    )

    # Send welcome photo and intro text
    try:
        await message.answer_photo(
            photo=FSInputFile("images/welcome_photo.jpg"),
            caption=(
                "Привет, я Павел Думбрао.\n\n"
                "Я делаю из идей — продукты, из продуктов — деньги.\n"
                "Запускаю AI-сервисы, воронки, автоматизации. Быстро, дерзко, по делу.\n\n"
                "Этот челлендж — не про «поиграться с нейросетями».\n"
                "Это про то, как встроить GPT в свою жизнь и заработать на этом.\n\n"
                "Если ты не хочешь быть заменён, тебе пора научиться управлять.\n\n"
                "Погнали."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        # If photo sending fails, just send text
        await message.answer(
            "Привет, я Павел Думбрао.\n\n"
            "Я делаю из идей — продукты, из продуктов — деньги.\n"
            "Запускаю AI-сервисы, воронки, автоматизации. Быстро, дерзко, по делу.\n\n"
            "Этот челлендж — не про «поиграться с нейросетями».\n"
            "Это про то, как встроить GPT в свою жизнь и заработать на этом.\n\n"
            "Если ты не хочешь быть заменён, тебе пора научиться управлять.\n\n"
            "Погнали.",
            parse_mode=ParseMode.MARKDOWN,
        )

    text = (
        "📌 *Важно перед стартом*\n\n"
        "1. *Подпишись на канал эксперта — без этого тебя не пустит в чат:*\n\n"
        "👉 [Канал Павла Думбрао](https://t.me/+olZLwPvR2RoyY2Uy)\n\n"
        "2. *После подписки заходи в чат челленджа:*\n\n"
        "👉 [Чат участников](https://t.me/+EO4WCUeMnV5hYjFi)\n\n"
        "_Подписка проверяется автоматически. Без неё — доступа к чату не будет._"
    )
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="✅ Проверить подписку", callback_data="check_sub"
                )
            ]
        ]
    )
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


@router.callback_query(lambda call: call.data.startswith("check_sub"))
async def callback_check_sub(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id

    # Check subscription only to channel
    subscribed = await check_subscription(callback.bot, user_id)
    if not subscribed:
        await callback.answer("❗️ Вы еще не подписаны на канал.", show_alert=True)
        return

    # Subscription confirmed:
    # Ensure user is in DB
    new_user = db.add_user(
        user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    # Referral bonus logic (grant once per invited user)
    user_data = db.get_user(user_id)
    if user_data:
        inviter_id = user_data.get("invited_by")
        ref_given = user_data.get("ref_bonus_given", 0)
    else:
        inviter_id = None
        ref_given = 0

    if inviter_id and ref_given == 0:
        # Add 50 points to inviter and mark bonus as given
        db.update_points(inviter_id, 50)
        db.set_ref_bonus_given(user_id)
        # Calculate number of referrals
        cur = db.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users WHERE invited_by = ?", (inviter_id,))
        referral_count = cur.fetchone()[0]
        # Fetch inviter's current points and challenge progress
        inviter_data = db.get_user(inviter_id)
        inviter_points = inviter_data["points"] if inviter_data else 0
        challenge_progress = (
            inviter_data["challenge_progress"]
            if inviter_data and "challenge_progress" in inviter_data
            else 0
        )
        # Prepare invited friend's username or first name
        invited_username = callback.from_user.username
        invited_name = callback.from_user.first_name
        display_name = (
            f"@{invited_username}" if invited_username else (invited_name or "друг")
        )
        if referral_count == 1:
            # First invite message
            try:
                photo = FSInputFile("images/first_invite.jpg")
                caption = (
                    "🎉 Ты пригласил первого друга!\n"
                    "+50 баллов на счёт.\n\n"
                    "Держи бонус: [📥 Скачать PDF]\n"
                    "Осталось ещё 4 до бесплатного входа в AI-клуб.\n"
                )
                await callback.bot.send_photo(
                    inviter_id,
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                # fallback to text
                await callback.bot.send_message(
                    inviter_id,
                    "🎉 Ты пригласил первого друга!\n"
                    "+50 баллов на счёт.\n\n"
                    "Держи бонус: [📥 Скачать PDF]\n"
                    "Осталось ещё 4 до бесплатного входа в AI-клуб.",
                )
            # Send the PDF bonus as document
            try:
                doc = FSInputFile("gift.pdf")
                await callback.bot.send_document(
                    inviter_id, document=doc, caption="📥 Скачать PDF"
                )
            except Exception:
                await callback.bot.send_message(
                    inviter_id,
                    "Не удалось отправить PDF-бонус. Обратитесь к администратору.",
                )
        else:
            # Subsequent invite message
            remaining = 5 - referral_count
            text = (
                f"💥 *Новый участник по твоей ссылке:* {display_name}\n"
                f"+50 баллов!\n"
                f"*Всего:* {inviter_points} баллов\n\n"
                f"Осталось ещё *{remaining}* друзей до клуба без оплаты!\n\n"
                f"*Промежуточный прогресс:*\n"
                f"🔄 *Прогресс:*\n\n"
                f"*Ты набрал:* {inviter_points} из 500\n"
                f"*Челлендж:* {challenge_progress} / 250\n"
                f"*Рефералы:* {referral_count} / 5\n\n"
                "Всё идёт по плану — продолжай!"
            )
            await callback.bot.send_message(
                inviter_id, text, parse_mode=ParseMode.MARKDOWN
            )

    # --- Referral Top N Prize Logic ---
    # Compute inviter's current rank (как в магазине)
    cur = db.conn.cursor()
    # Get current date
    today = datetime.date.today()

    if today.day == 1:
        # Reset top statuses at start of month
        try:
            db.reset_top_statuses()  # Implement this function in your db module
        except Exception:
            pass

    # Query for getting user rankings
    cur.execute(
        """
        SELECT u.user_id, COUNT(r.user_id) AS cnt
        FROM users u
        LEFT JOIN users r ON r.invited_by = u.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        """
    )
    all_rows = cur.fetchall()
    inviter_rank = None
    for idx, row in enumerate(all_rows, start=1):
        row_user_id = row["user_id"] if isinstance(row, (dict, sqlite3.Row)) else row[0]
        if row_user_id == inviter_id:
            inviter_rank = idx
            break
    inviter_premium = 0
    if inviter_id:
        inviter_data = db.get_user(inviter_id)
        if inviter_data and "premium" in inviter_data:
            inviter_premium = inviter_data["premium"]

    if today.day == 30:
        if inviter_rank == 1 and inviter_premium != "top1":
            try:
                await callback.bot.send_message(
                    inviter_id,
                    "🎉 Поздравляем! Вы заняли 1 место в рейтинге этого месяца! Напишите Павлу Думбрао (https://t.me/PavelDumbrao) в личные сообщения для получения доступа в группу.",
                )
            except Exception:
                pass
            db.set_premium(inviter_id, "top1")
        elif inviter_rank == 2 and inviter_premium != "top2":
            try:
                await callback.bot.send_message(
                    inviter_id,
                    "🥈 Поздравляем! Вы заняли 2 место в рейтинге этого месяца! Напишите Павлу Думбрао (https://t.me/PavelDumbrao) в личные сообщения для получения 20% скидки на продвинутый уровень.",
                )
            except Exception:
                pass
            db.set_premium(inviter_id, "top2")
        elif inviter_rank == 3 and inviter_premium != "top3":
            try:
                await callback.bot.send_message(
                    inviter_id,
                    "🥉 Поздравляем! Вы заняли 3 место в рейтинге этого месяца! Напишите Павлу Думбрао (https://t.me/PavelDumbrao) в личные сообщения для получения 10% скидки на продвинутый уровень.",
                )
            except Exception:
                pass
            db.set_premium(inviter_id, "top3")

    # Send second greeting with photo and inline "Старт" button
    photo = FSInputFile("images/second_photo.jpg")
    caption = (
        "Ты в GPT‑челлендже, который может реально изменить твою жизнь за 7 дней.\n\n"
        "🧠 Формат:\n"
        "– 15 минут в день\n"
        "– Видео + задание\n"
        "– Баллы, прогресс и призы\n\n"
        "Нажми *Старт*, чтобы начать первый день 👇"
    )
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Старт", callback_data="start_challenge")]
        ]
    )
    await callback.message.answer_photo(
        photo=photo, caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
    )

    await callback.answer()  # acknowledge callback


@router.callback_query(lambda call: call.data == "get_ref_link")
async def callback_get_ref_link(callback: types.CallbackQuery):
    user = callback.from_user
    user_id = user.id
    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    text = f"Ваша реферальная ссылка:\n{ref_link}"
    await callback.message.answer(text)
    await callback.answer()  # acknowledge callback


# Handler for "Старт" button callback
@router.callback_query(lambda call: call.data == "start_challenge")
async def callback_start_challenge(callback: types.CallbackQuery):
    # Send referral system message
    text = (
        "🚀 *Максимизируй свой результат с реферальной системой!* 🚀\n\n"
        "Заработай *50 баллов за каждого друга*, которого пригласишь в челлендж!\n\n"
        "📈 *Как это работает?*\n\n"
        "1. Приглашаешь друга — получаешь *50 баллов* на счёт.\n"
        "2. Твои друзья — твои бонусы. Чем больше людей приглашено, тем больше баллов ты зарабатываешь!\n"
        "3. Собрал *500 баллов* — *получаешь бесплатный доступ* в мой закрытый канал с эксклюзивными фишками и инсайдами!\n\n"
        "💥 *Используй рефералку* для быстрого накопления баллов. Это твой шанс попасть туда, где ты получишь реально рабочие инструменты и секреты, которые я применяю на практике!\n\n"
        "🔑 Не упусти возможность прокачать свои навыки быстрее, а заодно и получить доступ к самым крутым фишкам, которые помогут в бизнесе и жизни!"
    )
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="ПОЛУЧИТЬ РЕФЕРАЛЬНУЮ ССЫЛКУ",
                    callback_data="get_ref_link",
                )
            ]
        ]
    )
    await callback.message.answer(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()
    # Wait 15 seconds, then send the story bonus message
    await asyncio.sleep(15)
    story_text = (
        "🎉 *+50 баллов за сторис!* 🎉\n\n"
        "Ты хочешь получить *дополнительные баллы* и ускорить прохождение челленджа? Тогда вот что нужно сделать:\n\n"
        "✅ *Сделай сторис* с фото, где ты показываешь процесс или результат челленджа.\n\n"
        "✅ Отметь нас в сторис.\n\n"
        "✅ *Отправь скриншот* этой сторис в бота, чтобы получить *+50 баллов* на свой счёт!\n\n"
        "❗️ *Как это работает:*\n\n"
        "1. Сделай сторис с фото.\n"
        "2. Отметь нас в сторис.\n"
        "3. Отправь скриншот сторис в бота.\n"
        "4. Получи *50 бонусных баллов*.\n\n"
        "Баллы помогут тебе продвигаться по челленджу и получать доступ к новым урокам. Не упусти свой шанс! 💥"
        "Баллы за сторис начисляются только один раз, поэтому не забудь отправить скриншот!\n\n"
    )
    await callback.message.answer(story_text, parse_mode=ParseMode.MARKDOWN)

    await callback.message.answer_photo(
        photo=FSInputFile("images/menu.jpg"),
        caption="Выберите действие:",
        reply_markup=user_menu.main_menu,
    )


@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    points = user_data["points"] if user_data else 0
    premium = user_data["premium"] if user_data else 0
    challenge_progress = (
        user_data["challenge_progress"]
        if user_data and "challenge_progress" in user_data
        else 0
    )
    # Get referral count
    cur = db.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE invited_by = ?", (user_id,))
    referral_count = cur.fetchone()[0]
    remaining = 5 - referral_count
    # Calculate lesson-based points: each lesson gives 40 points
    lesson_point = challenge_progress * 40
    # Total possible lesson points
    max_lesson_points = len(lessons.LESSON_TEXTS) * 40
    text = (
        f"*💼 Общие баллы:* {points} баллов\n\n"
        f"*Баллы за уроки:* {lesson_point} / {max_lesson_points}\n"
        f"*Приглашено друзей:* {referral_count} / 5\n\n"
        f"Хочешь в AI-клуб бесплатно? Осталось пригласить *{remaining}* человек.\n\n"
    )
    if premium:
        text += "У тебя есть премиум доступ."
    else:
        text += "Премиум доступ не активирован."
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    points = user_data["points"] if user_data else 0

    # Compute the user's referral rank
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT u.user_id, COUNT(r.user_id) AS cnt
        FROM users u
        LEFT JOIN users r ON r.invited_by = u.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        """
    )
    all_rows = cur.fetchall()
    user_rank = None
    for idx, row in enumerate(all_rows, start=1):
        # row might be sqlite3.Row; extract user_id accordingly
        row_user_id = row["user_id"] if isinstance(row, (dict, sqlite3.Row)) else row[0]
        if row_user_id == user_id:
            user_rank = idx
            break

    # Build the shop description
    text = (
        "🎁 *Доступные призы:*\n\n"
        "🎫 *Вход в закрытый канал Павла на 1 мес* — 500 баллов\n"
        "🔒 *Постоянная скидка 10% на подписку* — 500 баллов\n"
        "📞 *Консультация с Павлом (1.5 ч)* — 800 баллов\n\n"
        "🥇 *ТОП-1 месяца* — Бесплатно (Переход на “Продвинутый уровень”)\n"
        "🥈 *ТОП-2 месяца* — Скидка 30%\n"
        "🥉 *ТОП-3 месяца* — Скидка 30%\n\n"
        "Для получения выбери кнопку ниже."
    )

    # Explicitly build the inline keyboard using a list of buttons
    buttons = []

    # Prize 1: Premium access for 1 month (500 points)
    buttons.append(
        [
            InlineKeyboardButton(
                text="🎫 Получить вход в закрытый канал за 500 баллов",
                callback_data="redeem_premium_points",
            )
        ]
    )

    # Prize 2: Permanent 10% discount (500 points)
    buttons.append(
        [
            InlineKeyboardButton(
                text="🔒 Получить постоянную скидку 10% за 500 баллов",
                callback_data="redeem_discount_points",
            )
        ]
    )

    # Prize 3: Consultation with Pavel (800 points)
    buttons.append(
        [
            InlineKeyboardButton(
                text="📞 Получить консультацию (1.5 ч) за 800 баллов",
                callback_data="redeem_consultation_points",
            )
        ]
    )

    # TOP prizes: only include buttons for which the user is eligible, and only during the last 7 days of the month
    today = datetime.date.today()
    year, month = today.year, today.month
    last_day = calendar.monthrange(year, month)[1]
    # Show TOP buttons only if current day is within the last 7 days of the month
    if today.day >= last_day - 6:
        if user_rank == 1:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="🥇 Я — ТОП-1 месяца (Переход на “Продвинутый уровень” бесплатно)",
                        callback_data="redeem_top1",
                    )
                ]
            )
        if user_rank == 2:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="🥈 Я — ТОП-2 месяца (Скидка 30% на “Продвинутый уровень”)",
                        callback_data="redeem_top2",
                    )
                ]
            )
        if user_rank == 3:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="🥉 Я — ТОП-3 месяца (Скидка 30% на “Продвинутый уровень”)",
                        callback_data="redeem_top3",
                    )
                ]
            )

    # Add "💸 Тарифы" button row
    buttons.append(
        [InlineKeyboardButton(text="💸 Тарифы", callback_data="show_tariffs")]
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("closed"))
async def cmd_closed(message: types.Message):
    promo_text = (
        "🔥 *ПОЛУЧИ ДОСТУП В МОЙ ЗАКРЫТЫЙ КАНАЛ И УЗНАЙ, КАК Я РАБОТАЮ С GPT* 🔥\n\n"
        "💡 Если хочешь увидеть, как я на самом деле использую GPT и другие инструменты для бизнеса — *ты здесь не случайно*.\n\n"
        "В *моём закрытом канале* я показываю *практическую сторону работы с AI*, а не витрины с теорией и скучными презентациями.\n\n"
        "---\n\n"
        "📦 *ЧТО ТЫ ПОЛУЧИШЬ:*\n\n"
        "1. *Готовые AI-сценарии*: Пошагово показываю, как я автоматизирую процессы с GPT и другими AI-инструментами. Просто повторяешь за мной — и получаешь результат.\n"
        "2. *Реальные кейсы*: Никакой воды — только практичные примеры того, как я строю воронки, генерирую трафик и создаю AI-решения.\n"
        "3. *Прямой доступ к инсайдам*: Разбираю все этапы процесса: от идеи до успешной продажи.\n"
        "4. *Тесты и эксперименты в реальном времени*: Я запускаю фишки и делюсь результатами, чтобы ты мог применить это сразу.\n"
        "5. *Секреты*: Реальные стратегии для увеличения продаж, автоматизации и масштабирования бизнеса.\n\n"
        "---\n\n"
        "⚡ *Что важно?* Здесь нет теории, только *работающие стратегии* и *инструменты*, которые я сам использую каждый день. Ты не просто смотришь, а внедряешь это в свой бизнес.\n\n"
        "Если ты готов делать, а не просто слушать, — тебе сюда.\n\n"
        "---\n\n"
        "🎯 *Как получить доступ?*\n\n"
        "1. 💳 Оплата — 2500 ₽ через бот.\n"
        "2. 🎯 Или накопи 500 баллов в *GPT-Челлендже* и получи доступ бесплатно!\n\n"
        "После оплаты или накопления баллов ты получишь доступ к каналу с *практическими кейсами* и *инсайдами*.\n\n"
        "💬 *Готов начать?* Нажми на кнопку ниже и выбери способ оплаты или накопления баллов.\n\n"
        "👉*Хочешь попасть?* Просто введи команду `/вход` в боте и забери свой доступ к каналу, где я показываю реальную работу с GPT.\n\n"
        "Не упусти свой шанс — действуй сейчас! 🔥"
    )
    # Send the closed-channel banner image
    await message.answer_photo(photo=FSInputFile("images/closed.jpg"))
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💳 Оплатить {config.PREMIUM_COST_RUB}₽",
                    callback_data="premium_pay",
                ),
                InlineKeyboardButton(
                    text=f"⚡️ {config.PREMIUM_COST_POINTS} баллов",
                    callback_data="premium_points",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💸 Тарифы",
                    callback_data="show_tariffs",
                ),
            ],
        ]
    )
    await message.answer(promo_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("entry"))
async def cmd_entry(message: types.Message):
    # Same as /closed
    await cmd_closed(message)


@router.message(Command("top"))
async def cmd_top(message: types.Message):
    # Get up to 10 users with their referral count (including zeros)
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT u.user_id, u.username, u.first_name,
               COUNT(r.user_id) AS cnt
        FROM users u
        LEFT JOIN users r ON r.invited_by = u.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        LIMIT 10
        """
    )
    rows = cur.fetchall()
    # Prepare rating text
    text_lines = ["🏆 Рейтинг за месяц:\n"]
    if not rows:
        text_lines.append("Нет пользователей.")
    else:
        rank = 1
        for row in rows:
            # Depending on row type, extract fields
            user_id_val = (
                row["user_id"]
                if isinstance(row, dict) or hasattr(row, "keys")
                else row[0]
            )
            count = (
                row["cnt"] if isinstance(row, dict) or hasattr(row, "keys") else row[3]
            )
            # Get display name
            user_data = db.get_user(user_id_val)
            if user_data:
                name = (
                    f"@{user_data['username']}"
                    if user_data.get("username")
                    else (user_data.get("first_name") or str(user_id_val))
                )
            else:
                name = str(user_id_val)
            text_lines.append(f"{rank}. {name} — {count} приглашений")
            rank += 1
    text_lines.append("\n🔁 Рейтинг обновляется каждый месяц. Топ-3 получают призы!")
    photo = FSInputFile("images/top.jpg")
    await message.answer_photo(photo=photo, caption="\n".join(text_lines))
    # await message.answer("\n".join(text_lines))


@router.message(Command("gift"))
async def cmd_gift(message: types.Message):
    user_data = db.get_user(message.from_user.id)
    cur = db.conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM users WHERE invited_by = ?", (message.from_user.id,)
    )
    referral_count = cur.fetchone()[0]
    if referral_count < 1:
        await message.answer(
            "🎁 Подарок станет доступен после приглашения хотя бы одного друга."
        )
    else:
        # Send the gift image before sending the PDF
        try:
            photo = FSInputFile("images/gift.jpg")
            await message.answer_photo(photo=photo)
        except Exception:
            pass
        # Send the gift PDF file
        try:
            doc = FSInputFile("gift.pdf")
            await message.answer_document(
                document=doc, caption="🎁 Ваш подарок - PDF файл."
            )
        except Exception as e:
            await message.answer(
                "Не удалось отправить подарок. Обратитесь к администратору."
            )


@router.message(lambda m: m.text and m.text.lower() in ["вход", "/вход"])
async def cmd_access_closed(message: types.Message):
    user_id = message.from_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get("premium"):
        # Check for existing one-time invite link
        invite_url = user_data.get("invite_link")
        if not invite_url:
            new_invite = await message.bot.create_chat_invite_link(
                chat_id=CLOSED_CHAT_URL, member_limit=1
            )
            invite_url = new_invite.invite_link
            db.set_invite_link(user_id, invite_url)
        await message.answer(f"Вот ссылка на закрытый чат: {invite_url}")
    else:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        text = "У вас нет премиум доступа. Получите премиум, чтобы войти."
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💸 Тарифы", callback_data="show_tariffs")]
            ]
        )
        await message.answer(text, reply_markup=kb)


@router.message(
    lambda m: m.text and m.text.lower() not in [w.lower() for w in lessons.CODE_WORDS]
)
async def handle_menu_text(message: types.Message):
    # Handle text input from the persistent menu keyboard
    text = message.text.lower()
    if text in ["баланс", "/баланс"]:
        return await cmd_balance(message)
    if text in ["магазин", "/магазин"]:
        return await cmd_shop(message)
    if text in ["пригласить", "/пригласить"]:
        return await referral.cmd_invite(message)
    if text in ["друзья", "/друзья"]:
        return await referral.cmd_friends(message)
    if text in ["подарок", "/подарок"]:
        return await cmd_gift(message)
    if text in ["топ", "/топ"]:
        return await cmd_top(message)
    if text in ["закрытый", "/закрытый"]:
        return await cmd_closed(message)
    if text in ["сотрудничество", "/сотрудничество"]:
        from aiogram.types import FSInputFile

        photo = FSInputFile("images/partner.jpg")
        await message.answer_photo(photo=photo)
        await message.answer(
            "🔥 Хотите партнёрство?\n\n"
            "– У вас продукт, связанный с AI / обучением?\n"
            "– Вы ведёте сообщество или канал?\n"
            "– Или хотите интеграцию в бота?\n\n"
            "Напишите: +7 912 201 3059 WA"
        )
        return
    if text in ["поддержка", "/поддержка"]:
        await message.answer("Для поддержки пишите сюда: https://t.me/PavelDumbrao")
        return
    # Unknown text - ignore silently
    return


# --- Tariffs and Payment Handlers ---


# Show tariff table
@router.callback_query(lambda c: c.data == "show_tariffs")
async def callback_show_tariffs(callback: types.CallbackQuery):
    tariff_text = (
        "*Тарифы на доступ в закрытый канал:*\n\n"
        "• 1 месяц — 2 490 ₽\n"
        "• 2 месяца — 3 980 ₽\n"
        "• 3 месяца — 5 470 ₽\n"
        "• 12 месяцев — 14 940 ₽\n\n"
        "Выберите тариф для оплаты:"
    )
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 мес – 2 490 ₽", callback_data="tariff_1")],
            [InlineKeyboardButton(text="2 мес – 3 980 ₽", callback_data="tariff_2")],
            [InlineKeyboardButton(text="3 мес – 5 470 ₽", callback_data="tariff_3")],
            [InlineKeyboardButton(text="12 мес – 14 940 ₽", callback_data="tariff_12")],
        ]
    )
    await callback.message.answer(
        tariff_text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()


# Payment URLs for each tariff
TARIFFS = {
    "tariff_1": 2490,
    "tariff_2": 3980,
    "tariff_3": 5470,
    "tariff_12": 14940,
}


# Generic handler for any tariff callback


@router.callback_query(lambda c: c.data.startswith("tariff_"))
async def handle_tariff(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tariff_key = callback.data  # e.g., "tariff_1"
    amount = TARIFFS.get(tariff_key)
    if not amount:
        await callback.answer("Выбран неверный тариф.", show_alert=True)
        return
    # Create and store payment label
    label = generate_payment_label(user_id)
    db.add_payment(label, user_id, amount)
    url = await create_payment_url(amount, label)
    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=f"💳 Оплатить {amount:,}".replace(",", " ") + " ₽",
                    url=url,
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🎟 У меня есть промокод",
                    callback_data=f"promo_{tariff_key}",
                )
            ],
        ]
    )
    await callback.message.answer(
        "Нажмите на кнопку ниже, чтобы перейти к оплате:",
        reply_markup=kb,
    )
    await callback.answer()


# Handler for promo-code on tariffs
@router.callback_query(lambda c: c.data.startswith("promo_"))
async def handle_tariff_promo(callback: types.CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    user_id = callback.from_user.id
    # Extract tariff_key from callback.data (format: 'promo_tariff_1' etc.)
    tariff_key = callback.data.split("promo_")[1]
    promo_context[user_id] = tariff_key

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="show_tariffs")]
        ]
    )
    await callback.message.answer("Введите ваш промокод.", reply_markup=kb)
    await callback.answer()


# --- Handlers for TOP prize redemption ---


@router.callback_query(lambda c: c.data == "redeem_top1")
async def redeem_top1_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Recompute user rank
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT u.user_id, COUNT(r.user_id) AS cnt
        FROM users u
        LEFT JOIN users r ON r.invited_by = u.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        """
    )
    all_rows = cur.fetchall()
    user_rank = None
    for idx, row in enumerate(all_rows, start=1):
        row_user_id = row["user_id"] if isinstance(row, (dict, sqlite3.Row)) else row[0]
        if row_user_id == user_id:
            user_rank = idx
            break

    if user_rank == 1:
        # Grant the free "Продвинутый уровень" and send closed chat link
        await callback.message.answer(
            f"🎉 Поздравляем! Вы — ТОП-1 этого месяца! Вам автоматически предоставлен доступ в закрытый канал.\n\n"
            f"Вот ссылка: {config.CLOSED_CHAT_URL}"
        )
        db.set_premium(user_id, True)
    else:
        await callback.answer(
            "⚠️ Для получения этого приза нужно быть ТОП-1.", show_alert=True
        )

    await callback.answer()


@router.callback_query(lambda c: c.data == "redeem_top2")
async def redeem_top2_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Recompute user rank
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT u.user_id, COUNT(r.user_id) AS cnt
        FROM users u
        LEFT JOIN users r ON r.invited_by = u.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        """
    )
    all_rows = cur.fetchall()
    user_rank = None
    for idx, row in enumerate(all_rows, start=1):
        row_user_id = row["user_id"] if isinstance(row, (dict, sqlite3.Row)) else row[0]
        if row_user_id == user_id:
            user_rank = idx
            break

    if user_rank == 2:
        # 30% discount for 1 month (2490 -> 1743)
        discount_percent = 30
        base_amount = 2490
        discounted_amount = int(base_amount * (100 - discount_percent) / 100)
        label = generate_payment_label(user_id)
        db.add_payment(label, user_id, discounted_amount)
        url = await create_payment_url(discounted_amount, label)
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=f"💳 Оплатить со скидкой {discounted_amount} ₽",
                        url=url,
                    )
                ]
            ]
        )
        await callback.message.answer(
            f"🥈 Поздравляем! Вы — ТОП-2 этого месяца и получили скидку 30% на «Продвинутый уровень» (1 месяц).\n\n"
            f"Для оплаты доступа по сниженной цене нажмите кнопку ниже:",
            reply_markup=kb,
        )
        db.set_premium(user_id, 2)
    else:
        await callback.answer(
            "⚠️ Для получения этого приза нужно быть ТОП-2.", show_alert=True
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "redeem_top3")
async def redeem_top3_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Recompute user rank
    cur = db.conn.cursor()
    cur.execute(
        """
        SELECT u.user_id, COUNT(r.user_id) AS cnt
        FROM users u
        LEFT JOIN users r ON r.invited_by = u.user_id
        GROUP BY u.user_id
        ORDER BY cnt DESC
        """
    )
    all_rows = cur.fetchall()
    user_rank = None
    for idx, row in enumerate(all_rows, start=1):
        row_user_id = row["user_id"] if isinstance(row, (dict, sqlite3.Row)) else row[0]
        if row_user_id == user_id:
            user_rank = idx
            break

    if user_rank == 3:
        # 30% discount for 1 month (2490 -> 1743)
        discount_percent = 30
        base_amount = 2490
        discounted_amount = int(base_amount * (100 - discount_percent) / 100)
        label = generate_payment_label(user_id)
        db.add_payment(label, user_id, discounted_amount)
        url = await create_payment_url(discounted_amount, label)
        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=f"💳 Оплатить со скидкой {discounted_amount} ₽",
                        url=url,
                    )
                ]
            ]
        )
        await callback.message.answer(
            f"🥉 Поздравляем! Вы — ТОП-3 этого месяца и получили скидку 30% на «Продвинутый уровень» (1 месяц).\n\n"
            f"Для оплаты доступа по сниженной цене нажмите кнопку ниже:",
            reply_markup=kb,
        )
        db.set_premium(user_id, 3)
    else:
        await callback.answer(
            "⚠️ Для получения этого приза нужно быть ТОП-3.", show_alert=True
        )
    await callback.answer()


# --- Handlers for shop point redemptions ---


@router.callback_query(lambda c: c.data == "redeem_premium_points")
async def redeem_premium_points_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get("points", 0) >= 500:
        db.update_points(user_id, -500)
        db.set_premium(user_id, True)
        await callback.message.answer(
            f"🎫 Поздравляем! Вы получили доступ в закрытый канал на 1 месяц.\n\n"
            f"Напишите мне в личные сообщения для получения доступа: @PavelDumbrao"
        )
    else:
        await callback.message.answer("Недостаточно баллов для получения доступа.")
    await callback.answer()


@router.callback_query(lambda c: c.data == "redeem_discount_points")
async def redeem_discount_points_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get("points", 0) >= 500:
        db.update_points(user_id, -500)
        # Mark in DB as having received a discount coupon (use premium=2)
        db.set_premium(user_id, 2)
        await callback.message.answer(
            "🔒 Поздравляем! Вы получили постоянную скидку 10% на подписку.\n\n"
            "Ваш купон: GPTDISCOUNT\n\n"
            "Используйте этот купон при оплате подписки."
        )
    else:
        await callback.message.answer("Недостаточно баллов для получения скидки.")
    await callback.answer()


@router.callback_query(lambda c: c.data == "redeem_consultation_points")
async def redeem_consultation_points_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get("points", 0) >= 800:
        db.update_points(user_id, -800)
        await callback.message.answer(
            "📞 Поздравляем! Вы получили консультацию с Павлом (1.5 ч).\n\n"
            "Для записи на консультацию напишите Павлу в Telegram: @PavelDumbrao и укажите, что вы получили консультацию через бот."
        )
    else:
        await callback.message.answer("Недостаточно баллов для получения консультации.")
    await callback.answer()
