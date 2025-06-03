from aiogram import Bot
from aiogram.types import ChatMember
import config


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """
    Check if a user is subscribed to the required channel.
    Returns True if subscribed, False otherwise.
    """
    try:
        member_channel = await bot.get_chat_member(config.CHANNEL_ID, user_id)
    except Exception:
        return False
    statuses_ok = ("member", "administrator", "creator")
    return member_channel.status in statuses_ok
