from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram import Update
from . import config
BOT_TOKEN = config.BOT_TOKEN
ADMIN_IDS = config.ADMIN_IDS
BOT_NAME = config.BOT_NAME
FORCE_JOIN_CHANNELS = config.FORCE_JOIN_CHANNELS
DEFAULT_API_CONFIG = config.DEFAULT_API_CONFIG
UPDATES_CHANNEL_ID = config.UPDATES_CHANNEL_ID
logger = config.logger
DATABASE_FILE = config.DATABASE_FILE
BACKUP_FILE = config.BACKUP_FILE
from .config.services import SERVICES_CONFIG
from .database.db_management import DatabaseManager
from .database.db_exclusions import ExclusionManager
from .error_handler import error_handler

# Import user handlers
from .handlers.user.start import start
from .handlers.user.dashboard import dashboard_command
from .handlers.user.tools import tools_command
from .handlers.user.credits import credits_command
from .handlers.user.referral import refer_command
from .handlers.user.shop import buy_command
from .handlers.user.support import support_command
from .handlers.user.help import help_command
from .handlers.user.stats import stats_command
from .handlers.user.balance import balance_command

# Import admin handlers
from .handlers.admin.dashboard import admin_command, show_admin_panel
from .handlers.admin.user_management import user_management_conversation
from .handlers.admin.broadcast_management import broadcast_conversation_handler
from .handlers.admin.exclusion_management import exclusion_management_conversation
from .handlers.user.shop import show_shop_category, show_item_confirmation, handle_and_redirect_purchase_request
from .handlers.user.exclusion_management import user_exclusion_management_conversation
from .handlers.common import button_handler, process_input
from .modules.broadcast_engine import handle_channel_post_broadcast

async def check_exclusion_and_process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Checks if the user's message is an exclusion before processing.
    If it is, sends the exclusion message and prevents further processing.
    Otherwise, calls the original process_input.
    """
    user_message = update.message.text
    exclusion = await ExclusionManager.get_exclusion(user_message)

    if exclusion:
        await update.message.reply_text(exclusion["message"])
        # Do not deduct ZC for excluded queries, as per requirement
        logger.info(f"User {update.message.from_user.id} queried an excluded item: '{user_message}'. Sent exclusion message.")
        return
    
    # If not an exclusion, proceed with normal input processing
    await process_input(update, context)

def register_handlers(application: Application) -> None:
    """Registers all command, message, and callback query handlers."""
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dashboard", dashboard_command))
    application.add_handler(CommandHandler("tools", tools_command))
    application.add_handler(CommandHandler("credits", credits_command))
    application.add_handler(CommandHandler("refer", refer_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("balance", balance_command))
    
    # Admin-only commands
    application.add_handler(CommandHandler("admin", admin_command, filters.User(ADMIN_IDS)))
    application.add_handler(CommandHandler("reload", reload_bot, filters.User(ADMIN_IDS))) # New reload command

    # Add conversation handlers
    application.add_handler(user_management_conversation)
    application.add_handler(broadcast_conversation_handler())
    application.add_handler(exclusion_management_conversation)
    application.add_handler(user_exclusion_management_conversation)

    # Add specific callback query handlers for shop categories and purchase flow
    application.add_handler(CallbackQueryHandler(show_shop_category, pattern="^shop_category_"))
    application.add_handler(CallbackQueryHandler(show_item_confirmation, pattern="^user_shop_select_"))
    application.add_handler(CallbackQueryHandler(handle_and_redirect_purchase_request, pattern="^user_shop_confirm_"))
    
    # Add general callback query handler (should be after specific ones to avoid conflicts)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Add message handlers - separate for admin and regular users
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), 
        check_exclusion_and_process_input  # Use the new wrapper function
    ))
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.User(ADMIN_IDS), 
        check_exclusion_and_process_input # Use the new wrapper function
    ))
    
    # Handler for channel posts from the updates channel
    application.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POST & filters.Chat(UPDATES_CHANNEL_ID),
        handle_channel_post_broadcast
    ))

    # Add error handler
    application.add_error_handler(error_handler)

async def reload_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Admin command to reload bot components and re-initialize the database.
    """
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Unauthorized access denied.")
        return

    await update.message.reply_text("🔄 Reloading bot components and re-initializing database...")
    logger.info(f"Admin {user_id} initiated bot reload.")

    try:
        # Re-initialize database
        DatabaseManager.initialize_db()
        from .database.db_shop import ensure_exclusion_slot_shop_item_exists
        await ensure_exclusion_slot_shop_item_exists() # Added await here
        logger.info("Database re-initialized.")

        # Clear existing handlers
        context.application.handlers.clear()
        logger.info("Existing handlers cleared.")

        # Re-register handlers
        register_handlers(context.application)
        logger.info("Handlers re-registered.")

        await update.message.reply_text("✅ Bot components reloaded successfully!")
        logger.info(f"Bot reload completed by admin {user_id}.")

    except Exception as e:
        logger.error(f"Error during bot reload by admin {user_id}: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Failed to reload bot components: {e}")

async def main() -> None:
    """Main function to start the bot"""
    import asyncio
    
    # Initialize database
    DatabaseManager.initialize_db()
    # Ensure shop items like Exclusion Slot exist
    from .database.db_shop import ensure_exclusion_slot_shop_item_exists
    await ensure_exclusion_slot_shop_item_exists() # Added await here
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    register_handlers(application)

    # Log startup information
    logger.info(f"🚀 {BOT_NAME} v2.2 starting...")
    logger.info(f"👑 Admin IDs: {ADMIN_IDS}")
    logger.info(f"🔒 Force join channels: {FORCE_JOIN_CHANNELS}")
    logger.info(f"⚡ Enhanced with pagination and improved error handling")
    logger.info(f"🛠️ Available tools: {len(SERVICES_CONFIG)}")
    logger.info(f"🔬 New tool: Deep Mobile Scan")
    logger.info(f"📄 Enhanced: Result pagination and file export")
    logger.info(f"💎 Credit system: Most tools free, Deep Scan premium")

    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        allowed_updates=filters.Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    # Keep the bot running
    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour, then continue
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    finally:
        # Clean shutdown
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def run_bot() -> None:
    """Wrapper function to run the async main function"""
    import asyncio
    import sys
    
    # Create a new event loop and set it as the current loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the main function in the new event loop
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
    finally:
        # Close the event loop
        loop.close()

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")