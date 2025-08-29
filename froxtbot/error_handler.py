import hashlib
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from .database.db_management import DatabaseManager
from .config import logger, DEBUG_MODE

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors and log them"""
    logger.error(f"Update {update} caused error {context.error}", exc_info=True)
    
    try:
        db = await DatabaseManager.load_db()
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(context.error).__name__,
            "error_message": str(context.error),
            "update_type": type(update).__name__ if update else "Unknown"
        }
        
        if "analytics" not in db:
            db["analytics"] = {"error_logs": []}
        if "error_logs" not in db["analytics"]:
            db["analytics"]["error_logs"] = []
            
        db["analytics"]["error_logs"].append(error_entry)
        db["analytics"]["error_logs"] = db["analytics"]["error_logs"][-50:]  # Keep last 50 errors
        await DatabaseManager.save_db(db)
    except Exception as e:
        logger.error(f"Failed to log error to database: {e}")

    # Try to send error message to user
    if update and isinstance(update, Update) and update.effective_message:
        try:
            error_message_for_user = (
                f"❌ System Error\n\n"
                f"⚠️ An unexpected error occurred. Our team has been notified.\n"
                f"🔄 Please try again in a few moments."
            )
            
            if DEBUG_MODE:
                error_message_for_user += f"\n\n📋 Details: `{context.error}`"
            else:
                error_id = hashlib.md5(str(context.error).encode()).hexdigest()[:8]
                error_message_for_user += f"\n\n🆔 Error ID: `{error_id}`"

            await update.effective_message.reply_text(
                text=error_message_for_user,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")