from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from db.db import get_pending_payments, set_payment_status, set_premium
from utils.yoomoney import check_payment
import logging


async def check_payments_job(bot: Bot):
    """
    Scheduled job to check pending YooMoney payments and activate premium for paid ones.
    """
    pending_payments = get_pending_payments()
    if not pending_payments:
        return
    for label, user_id, amount, created_at in pending_payments:
        # Check if payment link has expired (older than 24 hours)
        try:
            created_time = datetime.fromisoformat(created_at)
        except Exception as e:
            logging.exception(
                f"Error parsing created_at '{created_at}' for label {label}: {e}"
            )
            created_time = None
        if created_time:
            elapsed = (datetime.now() - created_time).total_seconds()
            if elapsed > 24 * 3600:
                # Mark as expired
                set_payment_status(label, "expired")
                continue
        # Check payment status via YooMoney API
        try:
            paid = await check_payment(label)
        except Exception as e:
            logging.exception(f"Error checking payment status for label {label}: {e}")
            paid = False
        if paid:
            # Mark as paid
            set_payment_status(label, "paid")
            # Grant premium to user
            set_premium(user_id, True)
            # Notify user about successful premium activation
            try:
                await bot.send_message(
                    user_id, "✅ Ваш платеж подтвержден! Премиум доступ активирован."
                )
            except Exception as e:
                logging.exception(
                    f"Error sending premium activation notice to user {user_id}: {e}"
                )
