from aiogram import Router, types
import db.db as db
import config
from utils import yoomoney
import logging

router = Router()


@router.callback_query(lambda c: c.data == "premium_pay")
async def premium_pay_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Check if user already premium
    user_data = db.get_user(user_id)
    if user_data and user_data.get("premium"):
        await callback.answer("У вас уже есть премиум доступ.", show_alert=True)
        return
    # Generate payment link and save pending payment
    try:
        label = yoomoney.generate_payment_label(user_id)
        pay_url = await yoomoney.create_payment_url(config.PREMIUM_COST_RUB, label)
        db.add_payment(label, user_id, config.PREMIUM_COST_RUB)
    except Exception as e:
        logging.exception(f"Error creating payment for user {user_id}: {e}")
        await callback.answer(
            "Не удалось создать платёжную ссылку. Попробуйте позже.", show_alert=True
        )
        return
    # Acknowledge callback
    await callback.answer()
    # Send payment link to user
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Оплатить премиум", url=pay_url)]
        ]
    )
    await callback.message.answer(
        "Нажмите кнопку ниже, чтобы оплатить премиум:", reply_markup=markup
    )
    # Optionally, remove inline keyboard from the shop message to prevent duplicate clicks
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logging.exception(
            f"Failed to remove reply markup for premium_pay_callback: {e}"
        )


@router.callback_query(lambda c: c.data == "premium_points")
async def premium_points_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data = db.get_user(user_id)
    if user_data and user_data.get("premium"):
        await callback.answer("У вас уже есть премиум доступ.", show_alert=True)
        return
    points = user_data["points"] if user_data else 0
    if points < config.PREMIUM_COST_POINTS:
        await callback.answer(
            "Недостаточно баллов для покупки премиума.", show_alert=True
        )
        return
    # Deduct points and grant premium
    try:
        db.update_points(user_id, -config.PREMIUM_COST_POINTS)
        db.set_premium(user_id, True)
    except Exception as e:
        logging.exception(
            f"Error activating premium via points for user {user_id}: {e}"
        )
        await callback.answer(
            "Ошибка при активации премиума. Попробуйте позже.", show_alert=True
        )
        return
    await callback.answer()
    await callback.message.answer(
        f"✅ Премиум доступ активирован! {config.PREMIUM_COST_POINTS} баллов списано с вашего баланса."
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        logging.exception(
            f"Failed to remove reply markup for premium_points_callback: {e}"
        )
