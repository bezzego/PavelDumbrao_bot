from aiogram import Router, types
import db.db as db
import config
from utils import yoomoney

router = Router()


@router.callback_query(lambda c: c.data == "premium_pay")
async def premium_pay_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Check if user already premium
    user_data = db.get_user(user_id)
    if user_data and user_data.get("premium"):
        await callback.answer("У вас уже есть премиум доступ.", show_alert=True)
        return
    # Generate payment link
    label = yoomoney.generate_payment_label(user_id)
    pay_url = await yoomoney.create_payment_url(config.PREMIUM_COST_RUB, label)
    # Save pending payment in DB
    db.add_payment(label, user_id, config.PREMIUM_COST_RUB)
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
    except:
        pass


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
    db.update_points(user_id, -config.PREMIUM_COST_POINTS)
    db.set_premium(user_id, True)
    await callback.answer()
    await callback.message.answer(
        "✅ Премиум доступ активирован! 500 баллов списано с вашего баланса."
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
