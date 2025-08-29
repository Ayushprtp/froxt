from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..config import ADMIN_IDS, FORCE_JOIN_CHANNELS, logger
from .keyboards import create_button, create_keyboard

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    # Check if effective_user exists
    if not update.effective_user:
        logger.warning("Update object doesn't have effective_user attribute")
        return False
        
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        return True

    not_joined_channels = []
    
    for channel in FORCE_JOIN_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined_channels.append(channel)
        except Exception as e:
            logger.error(f"Error checking channel membership for {channel}: {e}")
            continue

    if not_joined_channels:
        keyboard = []
        for channel in not_joined_channels:
            keyboard.append([create_button(
                f"Join {channel}", 
                url=f"https://t.me/{channel[1:]}", 
                style="premium"
            )])
        
        keyboard.append([create_button("✅ Check Again", "check_membership", style="success")])
        
        message_text = (
            "🔒 Access Required\n\n"
            "To use this bot, please join our channels:\n\n" +
            "\n".join([f"• {channel}" for channel in not_joined_channels]) + 
            "\n\nAfter joining, click 'Check Again' button below!"
        )
        
        if update.message:
            await update.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif update.callback_query:
            await update.callback_query.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return False

    return True
