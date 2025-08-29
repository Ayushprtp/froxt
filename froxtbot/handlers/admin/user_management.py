import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
)
from telegram.error import BadRequest
from ...database.db_users import UserManager
from ...database.db_history import get_all_query_history
from ...utils.keyboards import (
    create_keyboard, # Assuming this is the equivalent of build_user_list_menu, etc.
    build_user_list_menu,
    build_user_management_menu,
    build_role_selection_keyboard,
    build_cancel_keyboard,
)
from .dashboard import show_admin_panel # Assuming this is the equivalent of show_admin_dashboard

logger = logging.getLogger(__name__)

(
    LIST_USERS,
    VIEW_USER,
    AWAIT_SEARCH_QUERY,
    AWAIT_ZC_INPUT,
    AWAIT_ROLE_NAME,
    AWAIT_ROLE_DURATION,
) = range(6)


# Helper function to get user details for display
async def _get_user_display_text(user_id: int) -> str:
    user = await UserManager.get_user_profile(user_id)
    if user:
        return (
            f"Managing {user['full_name']} (@{user['username'] or 'N/A'})\n"
            f"ID: {user['user_id']}\n"
            f"Role: {user['role']}\n"
            f"ZC Balance: {user['zc_balance']}"
        )
    return "User not found."


async def start_user_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the user management conversation."""
    query = update.callback_query
    if query:
        await query.answer()
    await show_user_list(update, context)
    return LIST_USERS


async def show_user_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    """Displays a paginated list of users."""
    query = update.callback_query
    users = await UserManager.get_users_paginated(page=page, limit=10)
    total_users = await UserManager.get_user_count()
    keyboard = build_user_list_menu(users, page, total_users, limit=10)
    try:
        if query:
            await query.edit_message_text("👥 **User Management**", reply_markup=keyboard)
        else:
            await update.message.reply_text("👥 **User Management**", reply_markup=keyboard)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            logger.warning("Message not modified in show_user_list.")
        else:
            raise e


async def view_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the management menu for a selected user."""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    user = await UserManager.get_user_profile(user_id)
    keyboard = build_user_management_menu(user_id, user["is_banned"])
    await query.edit_message_text(
        await _get_user_display_text(user_id),
        reply_markup=keyboard,
    )
    return VIEW_USER


async def prompt_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the admin to enter a search query."""
    query = update.callback_query
    await query.answer()
    keyboard = build_cancel_keyboard("admin_users")
    await query.edit_message_text(
        "Enter the user ID or username to search for:", reply_markup=keyboard
    )
    return AWAIT_SEARCH_QUERY


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the search query and displays the result."""
    query_text = update.message.text
    user = await UserManager.search_user(query_text)
    if user:
        context.user_data["user_id"] = user["id"]
        keyboard = build_user_management_menu(user["id"], user["is_banned"])
        await update.message.reply_text(
            await _get_user_display_text(user["id"]),
            reply_markup=keyboard,
        )
        return VIEW_USER
    else:
        await update.message.reply_text("User not found.")
        await start_user_management(update, context) # Go back to user list
        return LIST_USERS


async def prompt_edit_zc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts the admin to enter a new ZC value."""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    context.user_data["user_id"] = user_id
    keyboard = build_cancel_keyboard(f"admin_user_select_{user_id}")
    await query.edit_message_text("Enter the new ZC balance:", reply_markup=keyboard)
    return AWAIT_ZC_INPUT


async def handle_edit_zc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the new ZC value and updates the database."""
    try:
        new_balance = float(update.message.text) # ZC can be float
        user_id = context.user_data["user_id"]
        await UserManager.update_user_credits(user_id, new_balance - (await UserManager.get_user(user_id))["credits"], "admin_edit_zc")
        # await get_all_query_history.log_admin_action(  # Commenting out as this function doesn't exist
        #     admin_user_id=update.effective_user.id,
        #     action=f"set_zc_balance_to_{new_balance}",
        #     target_user_id=user_id,
        # )
        await update.message.reply_text("✅ ZC balance updated.")
        keyboard = build_user_management_menu(user_id, (await UserManager.get_user_profile(user_id))["is_banned"])
        await update.message.reply_text(
            await _get_user_display_text(user_id),
            reply_markup=keyboard,
        )
        return VIEW_USER
    except ValueError:
        await update.message.reply_text("Invalid number. Please enter a valid number.")
        return AWAIT_ZC_INPUT


async def toggle_ban_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Toggles the ban status of a user."""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    user = await UserManager.get_user_profile(user_id)
    new_ban_status = not user["is_banned"]
    await UserManager.set_user_banned_status(user_id, new_ban_status)
        # await get_all_query_history.log_admin_action(  # Commenting out as this function doesn't exist
        #     admin_user_id=update.effective_user.id,
        #     action="ban" if new_ban_status else "unban",
        #     target_user_id=user_id,
        # )
    await query.edit_message_text(f"User has been {'banned' if new_ban_status else 'unbanned'}.")
    keyboard = build_user_management_menu(user_id, new_ban_status)
    await query.message.reply_text(
        await _get_user_display_text(user_id),
        reply_markup=keyboard,
    )
    return VIEW_USER


async def prompt_set_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Displays the role selection keyboard."""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[-1])
    context.user_data["user_id"] = user_id
    roles = await UserManager.get_all_roles()
    keyboard = build_role_selection_keyboard(user_id, roles)
    await query.edit_message_text("👑 Select the new role:", reply_markup=keyboard)
    return AWAIT_ROLE_NAME


async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the selected role and prompts for duration."""
    query = update.callback_query
    await query.answer()
    role_id = int(query.data.split("_")[3]) # Assuming callback data is like admin_role_select_<role_id>
    context.user_data["role_id"] = role_id
    keyboard = build_cancel_keyboard(f"admin_user_select_{context.user_data['user_id']}")
    await query.edit_message_text(
        "Enter the duration in days (0 for permanent):", reply_markup=keyboard
    )
    return AWAIT_ROLE_DURATION


async def handle_set_role_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the duration and updates the user's role."""
    try:
        duration = int(update.message.text)
        user_id = context.user_data["user_id"]
        role_id = context.user_data["role_id"]

        role = await UserManager.get_role_by_id(role_id)
        if not role:
            await update.message.reply_text(f"Error: Role with ID '{role_id}' not found.")
            return VIEW_USER

        await UserManager.promote_user(user_id, role_id, duration if duration > 0 else None)
        # await get_all_query_history.log_admin_action(  # Commenting out as this function doesn't exist
        #     admin_user_id=update.effective_user.id,
        #     action=f"set_role_to_{role['name']}_for_{duration}_days",
        #     target_user_id=user_id,
        # )
        await update.message.reply_text("✅ User role updated.")
        keyboard = build_user_management_menu(user_id, (await UserManager.get_user_profile(user_id))["is_banned"])
        await update.message.reply_text(
            await _get_user_display_text(user_id),
            reply_markup=keyboard,
        )
        return VIEW_USER
    except ValueError:
        await update.message.reply_text("Invalid number. Please enter a valid integer.")
        return AWAIT_ROLE_DURATION


async def end_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ends the conversation and returns to the main admin dashboard."""
    query = update.callback_query
    if query:
        await query.answer()
        await show_admin_panel(query) # Go back to admin dashboard
    else:
        await show_admin_panel(update.message) # Go back to admin dashboard
    context.user_data.clear()
    return ConversationHandler.END


user_management_conversation = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_user_management, pattern="^admin_users$")],
    states={
        LIST_USERS: [
            CallbackQueryHandler(view_user, pattern="^admin_user_select_"),
            CallbackQueryHandler(prompt_search, pattern="^admin_user_search$"),
            CallbackQueryHandler(show_user_list, pattern="^admin_user_page_"),
        ],
        VIEW_USER: [
            CallbackQueryHandler(prompt_edit_zc, pattern="^admin_user_editzc_"),
            CallbackQueryHandler(toggle_ban_status, pattern="^admin_user_(un)?ban_"),
            CallbackQueryHandler(prompt_set_role, pattern="^admin_user_setrole_"),
            CallbackQueryHandler(start_user_management, pattern="^admin_users$"), # Back to list
        ],
        AWAIT_SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)],
        AWAIT_ZC_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_zc)],
        AWAIT_ROLE_NAME: [CallbackQueryHandler(handle_role_selection, pattern="^admin_role_select_")],
        AWAIT_ROLE_DURATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_set_role_duration)
        ],
    },
    fallbacks=[
        CallbackQueryHandler(end_conversation, pattern="^admin_panel$"), # Back to admin panel
        CommandHandler("cancel", end_conversation),
        CommandHandler("start", end_conversation),
    ],
    map_to_parent={ConversationHandler.END: -1},
    per_message=True,
)
