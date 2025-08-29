import asyncio
import logging
from typing import List, Coroutine, Any

from telegram import Bot, Message, Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from ..database.db_management import DatabaseManager
from ..database.db_users import UserManager
from ..config import UPDATES_CHANNEL_ID

logger = logging.getLogger(__name__)

async def send_broadcast(
    bot: Bot,
    user_ids: List[int],
    message: Message
) -> (int, int):
    """
    Sends a message to a list of users with rate limiting.

    Args:
        bot: The bot instance.
        user_ids: A list of user IDs to send the message to.
        message: The message object to be broadcast.

    Returns:
        A tuple containing the number of successful and failed sends.
    """
    success_count = 0
    fail_count = 0
    
    for i in range(0, len(user_ids), 500):
        batch = user_ids[i:i+500]
        tasks: list[Coroutine[Any, Any, Any]] = []
        for user_id in batch:
            tasks.append(_send_copy(bot, user_id, message))
        
        results = await asyncio.gather(*tasks)
        success_count += sum(1 for r in results if r)
        fail_count += sum(1 for r in results if not r)
        
        if i + 500 < len(user_ids):
            logger.info(f"Batch of {len(batch)} sent. Waiting for 3 seconds...")
            await asyncio.sleep(3)
            
    return success_count, fail_count

async def _send_copy(bot: Bot, user_id: int, message: Message) -> bool:
    """A helper to copy a message and handle potential errors."""
    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat_id,
            message_id=message.message_id
        )
        logger.info(f"Successfully sent broadcast to {user_id}")
        return True
    except TelegramError as e:
        logger.error(f"Failed to send broadcast to {user_id}: {e}")
        return False

async def handle_channel_post_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles new channel posts from the updates channel and broadcasts them to all users.
    """
    message = update.channel_post
    if not message:
        logger.warning("Received channel post update without a message.")
        return

    user_ids = await UserManager.get_all_user_ids()
    
    # Exclude the channel itself from the broadcast list if it's also a user_id (unlikely but safe)
    if UPDATES_CHANNEL_ID in user_ids:
        user_ids.remove(UPDATES_CHANNEL_ID)

    success_count, fail_count = await send_broadcast(context.bot, user_ids, message)
    logger.info(f"Broadcast from channel post: {success_count} successful, {fail_count} failed.")
    
    # Optionally, send a confirmation to an admin or log it more prominently
    # For now, just log.