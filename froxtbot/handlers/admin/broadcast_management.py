import logging
from telegram import Update, Message
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler,
)
from ...config import ADMIN_IDS # Assuming admin_required decorator is not directly used, but admin check is done via filters.User(ADMIN_IDS)
from ...utils.keyboards import (
    create_keyboard, # Generic keyboard builder
    build_broadcast_menu,
    build_broadcast_target_menu,
    build_broadcast_confirmation_menu,
    build_cancel_keyboard,
)
from ...database.db_users import UserManager # Using UserManager to get user IDs by role
from ...database.db_management import DatabaseManager # Import DatabaseManager
from ...modules.broadcast_engine import send_broadcast
from .dashboard import show_admin_panel # For returning to admin dashboard

# Conversation states
(
    AWAIT_BROADCAST_MESSAGE,
    AWAIT_TARGET_SELECTION,
    AWAIT_CONFIRMATION,
) = range(3)

logger = logging.getLogger(__name__)

# The admin_required decorator is not directly available in froxtbot,
# so we'll rely on filters.User(ADMIN_IDS) in the ConversationHandler entry_points.

async def broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the main broadcast menu."""
    query = update.callback_query
    if query:
        await query.answer()
        keyboard = build_broadcast_menu()
        await query.edit_message_text(
            text="📢 **Broadcast Management**\n\n" \
                 "Select an option below to manage broadcasts.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    return ConversationHandler.END

async def new_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the process of creating a new broadcast."""
    query = update.callback_query
    if query:
        await query.answer()
        keyboard = build_cancel_keyboard("admin_panel") # Changed to admin_panel to go back to main admin menu
        await query.edit_message_text(
            text="Please send the message you want to broadcast. It can be text, an image with a caption, a video, or any other valid Telegram message.",
            reply_markup=keyboard,
        )
    return AWAIT_BROADCAST_MESSAGE

async def message_received_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the message to be broadcast."""
    context.user_data['broadcast_message'] = update.message
    roles = await UserManager.get_all_roles() # Get roles from UserManager
    keyboard = build_broadcast_target_menu(roles)
    await update.message.reply_text(
        text="Message received. Now, please choose who to broadcast this message to.",
        reply_markup=keyboard
    )
    return AWAIT_TARGET_SELECTION

async def target_selected_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the target audience selection."""
    query = update.callback_query
    await query.answer()
    target_id_str = query.data.split('_')[-1]
    context.user_data['broadcast_target_id'] = target_id_str
    
    broadcast_message: Message = context.user_data['broadcast_message']
    
    # Preview
    await query.edit_message_text(text="--- PREVIEW ---")
    await context.bot.copy_message(
        chat_id=query.message.chat_id,
        from_chat_id=broadcast_message.chat_id,
        message_id=broadcast_message.message_id
    )
    
    if target_id_str == "0":
        target_name = "Everyone"
    else:
        role = await UserManager.get_role_by_id(int(target_id_str))
        target_name = role["name"] if role else "Unknown Role"

    keyboard = build_broadcast_confirmation_menu()
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"Confirm broadcast to **{target_name}** users?",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    return AWAIT_CONFIRMATION


async def confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the final broadcast confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "broadcast_confirm_yes":
        target_id_str = context.user_data['broadcast_target_id']
        broadcast_message = context.user_data['broadcast_message']
        
        await query.edit_message_text(text=f"Fetching users for target: {target_id_str}...")
        
        user_ids = []
        if target_id_str == "0": # Broadcast to everyone
            user_ids = await UserManager.get_all_user_ids()
            target_name = "Everyone"
        else:
            target_role_id = int(target_id_str)
            db = await DatabaseManager.load_db()
            user_ids = [int(uid) for uid, udata in db["users"].items() if udata.get("role_id") == target_role_id]
            role = await UserManager.get_role_by_id(target_role_id)
            target_name = role["name"] if role else "Unknown Role"
            
        if not user_ids:
            await query.edit_message_text(text=f"No users found for {target_name}. Broadcast cancelled.")
            context.user_data.clear()
            return ConversationHandler.END

        await query.edit_message_text(text=f"Starting broadcast to {len(user_ids)} users ({target_name})...")
        
        success_count, fail_count = await send_broadcast(context.bot, user_ids, broadcast_message)
        
        await query.edit_message_text(
            text=f"📢 **Broadcast Complete**\n\n" \
                 f"Successfully sent: {success_count}\n" \
                 f"Failed to send: {fail_count}",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(text="Broadcast cancelled.")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the broadcast creation process."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="Broadcast creation cancelled.")
    else:
        await update.message.reply_text(text="Broadcast creation cancelled.")
    context.user_data.clear()
    await show_admin_panel(query if query else update.message)
    return ConversationHandler.END

async def back_to_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Wrapper to return to the admin panel."""
    query = update.callback_query
    if query:
        await query.answer()
    await show_admin_panel(query if query else update.message)
    context.user_data.clear()
    return ConversationHandler.END

def broadcast_conversation_handler() -> ConversationHandler:
    """Creates a conversation handler for the broadcast feature."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(new_broadcast_start, pattern="^broadcast_new$")],
        states={
            AWAIT_BROADCAST_MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND & filters.User(ADMIN_IDS), message_received_handler)],
            AWAIT_TARGET_SELECTION: [CallbackQueryHandler(target_selected_handler, pattern="^broadcast_target_")],
            AWAIT_CONFIRMATION: [CallbackQueryHandler(confirmation_handler, pattern="^broadcast_confirm_")],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_broadcast, pattern="^broadcast_cancel$"),
            CommandHandler("start", cancel_broadcast),
            CommandHandler("cancel", cancel_broadcast),
            CallbackQueryHandler(back_to_admin_panel, pattern="^admin_panel$"), # Allow returning to admin panel
        ],
        map_to_parent={
             ConversationHandler.END: -1
        },
    )
