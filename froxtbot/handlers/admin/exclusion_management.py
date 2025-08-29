import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from ...database.db_exclusions import ExclusionManager
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard, create_pagination_keyboard
from ...utils.pagination import PaginationManager
from ...config import ADMIN_IDS, DEFAULT_API_CONFIG

logger = logging.getLogger(__name__)

# States for ConversationHandler
ADD_EXCLUSION_VALUE, ADD_EXCLUSION_MESSAGE = range(2)
EDIT_EXCLUSION_SELECT, EDIT_EXCLUSION_VALUE, EDIT_EXCLUSION_MESSAGE = range(2, 5)
DELETE_EXCLUSION_SELECT = 5

async def show_exclusion_management_panel(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the exclusion management panel for admins."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return

    admin_menu = [
        [
            {"text": "➕ Add Exclusion", "callback_data": "admin_add_exclusion", "style": "success"},
            {"text": "📝 View/Edit Exclusions", "callback_data": "admin_view_exclusions", "style": "info"},
        ],
        [
            {"text": "🔙 Back to Admin Panel", "callback_data": "admin_panel", "style": "secondary"},
        ]
    ]

    await query.edit_message_text(
        text="🚫 EXCLUSION MANAGEMENT\n\n" 
             "Here you can manage the list of excluded queries. " 
             "If a user's query matches an item in this list, " 
             "the bot will return a predefined message instead of fetching API results, " 
             "and no credits will be deducted.",
        reply_markup=create_keyboard(admin_menu)
    )

async def add_exclusion_start(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation for adding a new exclusion."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    await query.edit_message_text(
        text="➕ ADD NEW EXCLUSION\n\n" 
             "Please send the exact query value to be excluded (e.g., 'mobile number 1234567890')."
    )
    context.user_data["admin_action"] = "add_exclusion_value"
    return ADD_EXCLUSION_VALUE

async def handle_add_exclusion_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the exclusion value."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    exclusion_value = update.message.text.strip()
    
    # Check for duplicate value
    existing_exclusion = await ExclusionManager.get_exclusion(exclusion_value)
    if existing_exclusion:
        await update.message.reply_text(
            f"❌ This exclusion value '{exclusion_value}' already exists. " 
            "Please try again with a different value or cancel.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "admin_add_exclusion", "style": "primary"}],
                [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
            ])
        )
        context.user_data.pop("admin_action", None)
        return ConversationHandler.END

    context.user_data["new_exclusion_value"] = exclusion_value
    await update.message.reply_text(
        text=f"Got it! The exclusion value will be: `{exclusion_value}`\n\n" 
             "Now, please send the message that users will receive when this query is excluded.",
        parse_mode='Markdown'
    )
    context.user_data["admin_action"] = "add_exclusion_message"
    return ADD_EXCLUSION_MESSAGE

async def handle_add_exclusion_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the exclusion message and save the exclusion."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    exclusion_message = update.message.text.strip()
    exclusion_value = context.user_data.get("new_exclusion_value")

    if not exclusion_value:
        await update.message.reply_text("❌ Error: Exclusion value not found. Please start over.",
                                        reply_markup=create_keyboard([
                                            [{"text": "➕ Add Exclusion", "callback_data": "admin_add_exclusion", "style": "success"}]
                                        ]))
        context.user_data.pop("admin_action", None)
        return ConversationHandler.END

    exclusion_no = await ExclusionManager.add_exclusion(user_id=user_id, value=exclusion_value, message=exclusion_message, added_by_admin=True)

    if exclusion_no:
        await update.message.reply_text(
            f"✅ Exclusion added successfully!\n\n" 
            f"ID: `{exclusion_no}`\n" 
            f"Value: `{exclusion_value}`\n" 
            f"Message: `{exclusion_message}`",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "➕ Add Another", "callback_data": "admin_add_exclusion", "style": "success"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ Failed to add exclusion. It might already exist or an error occurred.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "admin_add_exclusion", "style": "primary"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
    
    context.user_data.pop("new_exclusion_value", None)
    context.user_data.pop("admin_action", None)
    return ConversationHandler.END

async def view_exclusions(query, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
    """Display a paginated list of all exclusions."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return

    all_exclusions = await ExclusionManager.get_all_exclusions()
    
    if not all_exclusions:
        await query.edit_message_text(
            text="🚫 No exclusions found in the database.",
            reply_markup=create_keyboard([
                [{"text": "➕ Add Exclusion", "callback_data": "admin_add_exclusion", "style": "success"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
        return

    # Sort by exclusion_no for consistent pagination
    all_exclusions.sort(key=lambda x: x.get("exclusion_no", 0))

    page_size = DEFAULT_API_CONFIG["PAGINATION_SIZE"]
    
    paginated_data = PaginationManager.paginate_data(all_exclusions, page, page_size)
    
    if not paginated_data["page_data"]:
        await query.edit_message_text(
            text="❌ No exclusions found on this page.",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
        return

    message_text = "🚫 CURRENT EXCLUSIONS\n\n"
    for ex in paginated_data["page_data"]:
        message_text += (
            f"ID: `{ex.get('exclusion_no', 'N/A')}`\n" 
            f"Value: `{ex.get('value', 'N/A')}`\n" 
            f"Message: `{ex.get('message', 'N/A')}`\n" 
            f"Added By: `{ex.get('added_by', 'N/A')}` (Admin: {ex.get('added_by_admin', False)})\n" 
            f"Timestamp: `{ex.get('timestamp', 'N/A')}`\n" 
            f"Slot Owner: `{ex.get('slot_owner', 'N/A')}`\n" 
            f"-----------------------------------\n"
        )
    
    message_text += f"📄 Page {paginated_data['current_page']}/{paginated_data['total_pages']}\n"
    message_text += f"📊 Total Exclusions: {paginated_data['total_items']}\n\n"

    pagination_buttons = create_pagination_keyboard(
        paginated_data["current_page"],
        paginated_data["total_pages"],
        "admin_view_exclusions_page"
    )
    
    action_buttons = [
        [{"text": "✏️ Edit Exclusion", "callback_data": "admin_edit_exclusion_select", "style": "primary"}],
        [{"text": "🗑️ Delete Exclusion", "callback_data": "admin_delete_exclusion_select", "style": "danger"}],
        [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
    ]
    
    final_keyboard = pagination_buttons + action_buttons

    await query.edit_message_text(
        text=message_text,
        parse_mode='Markdown',
        reply_markup=create_keyboard(final_keyboard)
    )

async def handle_view_exclusions_pagination(query, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle pagination for viewing exclusions."""
    parts = callback_data.split('_')
    page = int(parts[-1])
    await view_exclusions(query, context, page)

async def edit_exclusion_select(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt admin to select an exclusion to edit."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    await query.edit_message_text(
        text="✏️ EDIT EXCLUSION\n\n" 
             "Please send the `ID` of the exclusion you want to edit.",
        parse_mode='Markdown',
        reply_markup=create_keyboard([
            [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
        ])
    )
    context.user_data["admin_action"] = "edit_exclusion_select"
    return EDIT_EXCLUSION_SELECT

async def handle_edit_exclusion_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for selecting an exclusion to edit."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    try:
        exclusion_no = int(update.message.text.strip())
        exclusion = await ExclusionManager.get_exclusion_by_id(exclusion_no)

        if not exclusion:
            await update.message.reply_text(
                f"❌ Exclusion with ID `{exclusion_no}` not found. Please try again or cancel.",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": "admin_edit_exclusion_select", "style": "primary"}],
                    [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
                ])
            )
            context.user_data.pop("admin_action", None)
            return ConversationHandler.END
        
        context.user_data["edit_exclusion_no"] = exclusion_no
        context.user_data["original_exclusion_value"] = exclusion["value"]
        context.user_data["original_exclusion_message"] = exclusion["message"]

        await update.message.reply_text(
            f"✏️ Editing Exclusion ID: `{exclusion_no}`\n" 
            f"Current Value: `{exclusion['value']}`\n" 
            f"Current Message: `{exclusion['message']}`\n\n" 
            "Please send the **new value** for this exclusion.",
            parse_mode='Markdown'
        )
        context.user_data["admin_action"] = "edit_exclusion_value"
        return EDIT_EXCLUSION_VALUE

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ID. Please send a number.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "admin_edit_exclusion_select", "style": "primary"}],
                [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
            ])
        )
        context.user_data.pop("admin_action", None)
        return ConversationHandler.END

async def handle_edit_exclusion_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the new exclusion value."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    new_value = update.message.text.strip()
    exclusion_no = context.user_data.get("edit_exclusion_no")

    if not exclusion_no:
        await update.message.reply_text("❌ Error: Exclusion ID not found. Please start over.",
                                        reply_markup=create_keyboard([
                                            [{"text": "✏️ Edit Exclusion", "callback_data": "admin_edit_exclusion_select", "style": "primary"}]
                                        ]))
        context.user_data.pop("admin_action", None)
        return ConversationHandler.END
    
    # Check for duplicate value if it's different from original
    original_value = context.user_data.get("original_exclusion_value")
    if new_value.lower() != original_value.lower():
        existing_exclusion = await ExclusionManager.get_exclusion(new_value)
        if existing_exclusion and existing_exclusion.get("exclusion_no") != exclusion_no:
            await update.message.reply_text(
                f"❌ This exclusion value '{new_value}' already exists for another exclusion. " 
                "Please try again with a different value or cancel.",
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": "admin_edit_exclusion_select", "style": "primary"}],
                    [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
                ])
            )
            context.user_data.pop("admin_action", None)
            return ConversationHandler.END

    context.user_data["new_exclusion_value"] = new_value
    await update.message.reply_text(
        f"Got it! New value will be: `{new_value}`\n\n" 
        "Now, please send the **new message** for this exclusion.",
        parse_mode='Markdown'
    )
    context.user_data["admin_action"] = "edit_exclusion_message"
    return EDIT_EXCLUSION_MESSAGE

async def handle_edit_exclusion_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the new exclusion message and update the exclusion."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    new_message = update.message.text.strip()
    exclusion_no = context.user_data.get("edit_exclusion_no")
    new_value = context.user_data.get("new_exclusion_value")

    if not exclusion_no or not new_value:
        await update.message.reply_text("❌ Error: Exclusion ID or new value not found. Please start over.",
                                        reply_markup=create_keyboard([
                                            [{"text": "✏️ Edit Exclusion", "callback_data": "admin_edit_exclusion_select", "style": "primary"}]
                                        ]))
        context.user_data.pop("admin_action", None)
        return ConversationHandler.END

    success = await ExclusionManager.update_exclusion(
        exclusion_no=exclusion_no,
        new_value=new_value,
        new_message=new_message,
        user_id=user_id,
        is_admin=True
    )

    if success:
        await update.message.reply_text(
            f"✅ Exclusion ID `{exclusion_no}` updated successfully!\n\n" 
            f"New Value: `{new_value}`\n" 
            f"New Message: `{new_message}`",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "📝 View Exclusions", "callback_data": "admin_view_exclusions", "style": "info"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update exclusion. An error occurred or the value might be a duplicate.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "admin_edit_exclusion_select", "style": "primary"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
    
    context.user_data.pop("edit_exclusion_no", None)
    context.user_data.pop("new_exclusion_value", None)
    context.user_data.pop("original_exclusion_value", None)
    context.user_data.pop("original_exclusion_message", None)
    context.user_data.pop("admin_action", None)
    return ConversationHandler.END

async def delete_exclusion_select(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt admin to select an exclusion to delete."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    await query.edit_message_text(
        text="🗑️ DELETE EXCLUSION\n\n" 
             "Please send the `ID` of the exclusion you want to delete.",
        parse_mode='Markdown',
        reply_markup=create_keyboard([
            [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
        ])
    )
    context.user_data["admin_action"] = "delete_exclusion_select"
    return DELETE_EXCLUSION_SELECT

async def handle_delete_exclusion_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for selecting an exclusion to delete and ask for confirmation."""
    user_id = update.message.from_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    try:
        exclusion_no = int(update.message.text.strip())
        exclusion = await ExclusionManager.get_exclusion_by_id(exclusion_no)

        if not exclusion:
            await update.message.reply_text(
                f"❌ Exclusion with ID `{exclusion_no}` not found. Please try again or cancel.",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": "admin_delete_exclusion_select", "style": "primary"}],
                    [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
                ])
            )
            context.user_data.pop("admin_action", None)
            return ConversationHandler.END
        
        context.user_data["delete_exclusion_no"] = exclusion_no

        await update.message.reply_text(
            f"🗑️ Confirm Deletion\n\n" 
            f"Are you sure you want to delete exclusion ID `{exclusion_no}`?\n" 
            f"Value: `{exclusion['value']}`\n" 
            f"Message: `{exclusion['message']}`",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "✅ Yes, Delete", "callback_data": f"admin_delete_exclusion_confirm_{exclusion_no}", "style": "danger"}],
                [{"text": "❌ No, Cancel", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
        context.user_data.pop("admin_action", None) # Clear admin_action as we are now waiting for a callback query
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ID. Please send a number.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "admin_delete_exclusion_select", "style": "primary"}],
                [{"text": "🚫 Cancel", "callback_data": "admin_exclusion_management", "style": "danger"}]
            ])
        )
        context.user_data.pop("admin_action", None)
        return ConversationHandler.END

async def delete_exclusion_confirmed(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delete the exclusion after confirmation."""
    user_id = query.from_user.id
    if user_id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return ConversationHandler.END

    parts = query.data.split('_')
    exclusion_no = int(parts[-1])

    success = await ExclusionManager.delete_exclusion(exclusion_no=exclusion_no, user_id=user_id, is_admin=True)

    if success:
        await query.edit_message_text(
            f"✅ Exclusion ID `{exclusion_no}` deleted successfully!",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "📝 View Exclusions", "callback_data": "admin_view_exclusions", "style": "info"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ Failed to delete exclusion. It might not exist or an error occurred.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "admin_delete_exclusion_select", "style": "primary"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "admin_exclusion_management", "style": "secondary"}]
            ])
        )
    
    context.user_data.pop("delete_exclusion_no", None)
    return ConversationHandler.END

# Add a new state handler for delete exclusion confirmation
async def handle_delete_exclusion_confirm(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the delete exclusion confirmation callback."""
    return await delete_exclusion_confirmed(query, context)

# Conversation handler for adding/editing/deleting exclusions
exclusion_management_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(add_exclusion_start, pattern="^admin_add_exclusion$"),
        CallbackQueryHandler(edit_exclusion_select, pattern="^admin_edit_exclusion_select$"),
        CallbackQueryHandler(delete_exclusion_select, pattern="^admin_delete_exclusion_select$"),
    ],
    states={
        ADD_EXCLUSION_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_exclusion_value)],
        ADD_EXCLUSION_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_exclusion_message)],
        EDIT_EXCLUSION_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_exclusion_select)],
        EDIT_EXCLUSION_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_exclusion_value)],
        EDIT_EXCLUSION_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_exclusion_message)],
        DELETE_EXCLUSION_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_exclusion_select)],
    },
    fallbacks=[
        CallbackQueryHandler(show_exclusion_management_panel, pattern="^admin_exclusion_management$"),
        CallbackQueryHandler(handle_delete_exclusion_confirm, pattern="^admin_delete_exclusion_confirm_"),
        CallbackQueryHandler(lambda q, c: ConversationHandler.END, pattern="^admin_panel$"), # Allow returning to admin panel
    ],
    map_to_parent={
        ConversationHandler.END: "admin_panel" # Return to admin panel after conversation ends
    }
)