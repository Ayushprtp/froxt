import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from ...database.db_exclusions import ExclusionManager
from ...database.db_users import UserManager
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard, create_pagination_keyboard
from ...utils.pagination import PaginationManager
from ...config import DEFAULT_API_CONFIG

logger = logging.getLogger(__name__)

# States for ConversationHandler
FILL_EXCLUSION_VALUE, FILL_EXCLUSION_MESSAGE = range(2)
EDIT_USER_EXCLUSION_SELECT, EDIT_USER_EXCLUSION_VALUE, EDIT_USER_EXCLUSION_MESSAGE = range(2, 5)
DELETE_USER_EXCLUSION_CONFIRM = 5
CLEAR_USER_EXCLUSION_CONFIRM = 6

async def show_user_exclusion_management_panel(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's exclusion management panel."""
    user_id = query.from_user.id
    user_exclusions = await ExclusionManager.get_user_exclusions(user_id)
    num_slots = len(user_exclusions)
    num_filled_slots = sum(1 for ex in user_exclusions if not ex.get("is_placeholder", True))
    num_empty_slots = num_slots - num_filled_slots

    menu_buttons = []
    if num_empty_slots > 0:
        menu_buttons.append([{"text": f"📝 Fill Empty Slot ({num_empty_slots} available)", "callback_data": "user_fill_exclusion_slot", "style": "success"}])
    
    if num_filled_slots > 0:
        menu_buttons.append([
            {"text": "👀 View My Exclusions", "callback_data": "user_view_exclusions", "style": "info"},
            {"text": "✏️ Edit Exclusion", "callback_data": "user_edit_exclusion_select", "style": "primary"},
        ])
        menu_buttons.append([
            {"text": "🗑️ Delete Exclusion", "callback_data": "user_delete_exclusion_select", "style": "danger"},
            {"text": "🔄 Clear Slot", "callback_data": "user_clear_exclusion_slot_select", "style": "warning"},
        ])
    
    menu_buttons.append([{"text": "➕ Buy More Slots (100 ZC)", "callback_data": "buy_credits", "style": "premium"}])
    menu_buttons.append([{"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"}])

    await query.edit_message_text(
        text=f"🚫 MY EXCLUSION SLOTS\n\n" 
             f"You currently have **{num_slots}** exclusion slots.\n"
             f"**{num_filled_slots}** filled, **{num_empty_slots}** empty.\n\n"
             "Manage your custom excluded queries here. Queries matching your exclusions will return a custom message and will not deduct ZC.",
        parse_mode='Markdown',
        reply_markup=create_keyboard(menu_buttons)
    )

async def view_user_exclusions(query, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
    """Display a paginated list of the user's exclusions."""
    user_id = query.from_user.id
    all_user_exclusions = await ExclusionManager.get_user_exclusions(user_id)
    
    if not all_user_exclusions:
        await query.edit_message_text(
            text="🚫 You have no exclusion slots or they are all empty. "
                 "Purchase a slot or fill an existing one to see it here.",
            reply_markup=create_keyboard([
                [{"text": "➕ Buy Exclusion Slot", "callback_data": "buy_credits", "style": "premium"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        return

    # Sort by exclusion_no for consistent pagination
    all_user_exclusions.sort(key=lambda x: x.get("exclusion_no", 0))

    db = await DatabaseManager.load_db()
    page_size = db["api_config"].get("PAGINATION_SIZE", DEFAULT_API_CONFIG["PAGINATION_SIZE"])
    
    paginated_data = PaginationManager.paginate_data(all_user_exclusions, page, page_size)
    
    if not paginated_data["page_data"]:
        await query.edit_message_text(
            text="❌ No exclusions found on this page.",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        return

    message_text = "🚫 YOUR EXCLUSIONS\n\n"
    for ex in paginated_data["page_data"]:
        status = "Empty (Placeholder)" if ex.get("is_placeholder", True) else "Filled"
        message_text += (
            f"ID: `{ex.get('exclusion_no', 'N/A')}`\n"
            f"Status: `{status}`\n"
            f"Value: `{ex.get('value', 'N/A')}`\n"
            f"Message: `{ex.get('message', 'N/A')}`\n"
            f"Added: `{ex.get('timestamp', 'N/A')}`\n"
            f"-----------------------------------\n"
        )
    
    message_text += f"📄 Page {paginated_data['current_page']}/{paginated_data['total_pages']}\n"
    message_text += f"📊 Total Slots: {paginated_data['total_items']}\n\n"

    pagination_buttons = create_pagination_keyboard(
        paginated_data["current_page"],
        paginated_data["total_pages"],
        "user_view_exclusions_page"
    )
    
    action_buttons = [
        [{"text": "📝 Fill Empty Slot", "callback_data": "user_fill_exclusion_slot", "style": "success"}],
        [{"text": "✏️ Edit Exclusion", "callback_data": "user_edit_exclusion_select", "style": "primary"}],
        [{"text": "🗑️ Delete Exclusion", "callback_data": "user_delete_exclusion_select", "style": "danger"}],
        [{"text": "🔄 Clear Slot", "callback_data": "user_clear_exclusion_slot_select", "style": "warning"}],
        [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
    ]
    
    final_keyboard = pagination_buttons + action_buttons

    await query.edit_message_text(
        text=message_text,
        parse_mode='Markdown',
        reply_markup=create_keyboard(final_keyboard)
    )

async def handle_user_view_exclusions_pagination(query, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle pagination for viewing user exclusions."""
    parts = callback_data.split('_')
    page = int(parts[-1])
    await view_user_exclusions(query, context, page)

async def fill_exclusion_slot_start(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation for filling an empty exclusion slot."""
    user_id = query.from_user.id
    user_exclusions = await ExclusionManager.get_user_exclusions(user_id)
    empty_slots = [ex for ex in user_exclusions if ex.get("is_placeholder", True)]

    if not empty_slots:
        await query.edit_message_text(
            text="❌ You have no empty exclusion slots to fill. "
                 "Purchase a new slot or clear an existing one.",
            reply_markup=create_keyboard([
                [{"text": "➕ Buy Exclusion Slot", "callback_data": "buy_credits", "style": "premium"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        return ConversationHandler.END

    # If there's only one empty slot, automatically select it
    if len(empty_slots) == 1:
        context.user_data["fill_exclusion_no"] = empty_slots[0]["exclusion_no"]
        await query.edit_message_text(
            text=f"📝 FILL EXCLUSION SLOT (ID: `{empty_slots[0]['exclusion_no']}`)\n\n" 
                 "Please send the exact query value to be excluded (e.g., 'mobile number 1234567890').",
            parse_mode='Markdown'
        )
        context.user_data["user_action"] = "fill_exclusion_value"
        return FILL_EXCLUSION_VALUE
    else:
        # Offer a choice if multiple empty slots
        buttons = [[{"text": f"Slot ID: {ex['exclusion_no']}", "callback_data": f"user_select_fill_slot_{ex['exclusion_no']}", "style": "info"}] for ex in empty_slots]
        buttons.append([{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}] )
        await query.edit_message_text(
            text="📝 FILL EXCLUSION SLOT\n\n" 
                 "You have multiple empty slots. Please select which one you want to fill:",
            reply_markup=create_keyboard(buttons)
        )
        context.user_data["user_action"] = "select_fill_slot" # Custom action to handle selection
        return FILL_EXCLUSION_VALUE # Stay in this state to receive callback or message

async def handle_select_fill_slot(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle selection of an empty slot to fill."""
    exclusion_no = int(query.data.split('_')[-1])
    context.user_data["fill_exclusion_no"] = exclusion_no
    await query.edit_message_text(
        text=f"📝 FILL EXCLUSION SLOT (ID: `{exclusion_no}`)\n\n" 
             "Please send the exact query value to be excluded (e.g., 'mobile number 1234567890').",
        parse_mode='Markdown'
    )
    context.user_data["user_action"] = "fill_exclusion_value"
    return FILL_EXCLUSION_VALUE

async def handle_fill_exclusion_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the exclusion value when filling a slot."""
    user_id = update.message.from_user.id
    exclusion_value = update.message.text.strip()
    exclusion_no = context.user_data.get("fill_exclusion_no")

    if not exclusion_no:
        await update.message.reply_text("❌ Error: Slot ID not found. Please start over.",
                                        reply_markup=create_keyboard([
                                            [{"text": "📝 Fill Empty Slot", "callback_data": "user_fill_exclusion_slot", "style": "success"}]
                                        ]))
        context.user_data.pop("user_action", None)
        return ConversationHandler.END
    
    # Check for duplicate value
    existing_exclusion = await ExclusionManager.get_exclusion(exclusion_value)
    if existing_exclusion and existing_exclusion.get("exclusion_no") != exclusion_no:
        await update.message.reply_text(
            f"❌ This exclusion value '{exclusion_value}' already exists for another exclusion. "
            "Please try again with a different value or cancel.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_fill_exclusion_slot", "style": "primary"}],
                [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
            ])
        )
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

    context.user_data["new_exclusion_value"] = exclusion_value
    await update.message.reply_text(
        text=f"Got it! The exclusion value will be: `{exclusion_value}`\n\n" 
             "Now, please send the message that users will receive when this query is excluded.",
        parse_mode='Markdown'
    )
    context.user_data["user_action"] = "fill_exclusion_message"
    return FILL_EXCLUSION_MESSAGE

async def handle_fill_exclusion_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the exclusion message and fill the slot."""
    user_id = update.message.from_user.id
    exclusion_message = update.message.text.strip()
    exclusion_no = context.user_data.get("fill_exclusion_no")
    exclusion_value = context.user_data.get("new_exclusion_value")

    if not exclusion_no or not exclusion_value:
        await update.message.reply_text("❌ Error: Slot ID or value not found. Please start over.",
                                        reply_markup=create_keyboard([
                                            [{"text": "📝 Fill Empty Slot", "callback_data": "user_fill_exclusion_slot", "style": "success"}]
                                        ]))
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

    success = await ExclusionManager.fill_exclusion_slot(
        exclusion_no=exclusion_no,
        user_id=user_id,
        value=exclusion_value,
        message=exclusion_message
    )

    if success:
        await update.message.reply_text(
            f"✅ Exclusion slot `{exclusion_no}` filled successfully!\n\n" 
            f"Value: `{exclusion_value}`\n"
            f"Message: `{exclusion_message}`",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "👀 View My Exclusions", "callback_data": "user_view_exclusions", "style": "info"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ Failed to fill exclusion slot. It might not exist, not be owned by you, or the value is a duplicate.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_fill_exclusion_slot", "style": "primary"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    
    context.user_data.pop("fill_exclusion_no", None)
    context.user_data.pop("new_exclusion_value", None)
    context.user_data.pop("user_action", None)
    return ConversationHandler.END

async def edit_user_exclusion_select(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt user to select an exclusion to edit."""
    user_id = query.from_user.id
    user_exclusions = await ExclusionManager.get_user_exclusions(user_id)
    filled_exclusions = [ex for ex in user_exclusions if not ex.get("is_placeholder", True)]

    if not filled_exclusions:
        await query.edit_message_text(
            text="❌ You have no filled exclusion slots to edit. "
                 "Fill an empty slot first.",
            reply_markup=create_keyboard([
                [{"text": "📝 Fill Empty Slot", "callback_data": "user_fill_exclusion_slot", "style": "success"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        return ConversationHandler.END

    buttons = [[{"text": f"ID: {ex['exclusion_no']} - {ex['value']}", "callback_data": f"user_select_edit_slot_{ex['exclusion_no']}", "style": "info"}] for ex in filled_exclusions]
    buttons.append([{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}])

    await query.edit_message_text(
        text="✏️ EDIT EXCLUSION\n\n" 
             "Please select the `ID` of the exclusion you want to edit, or send the ID directly.",
        parse_mode='Markdown',
        reply_markup=create_keyboard(buttons)
    )
    context.user_data["user_action"] = "edit_exclusion_select"
    return EDIT_USER_EXCLUSION_SELECT

async def handle_edit_user_exclusion_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for selecting an exclusion to edit."""
    user_id = update.message.from_user.id
    try:
        exclusion_no = int(update.message.text.strip())
        exclusion = await ExclusionManager.get_exclusion_by_id(exclusion_no)

        if not exclusion or exclusion.get("slot_owner") != user_id or exclusion.get("is_placeholder", True):
            await update.message.reply_text(
                f"❌ Exclusion with ID `{exclusion_no}` not found, not owned by you, or is empty. Please try again or cancel.",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": "user_edit_exclusion_select", "style": "primary"}],
                    [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
                ])
            )
            context.user_data.pop("user_action", None)
            return ConversationHandler.END
        
        context.user_data["edit_exclusion_no"] = exclusion_no
        context.user_data["original_exclusion_value"] = exclusion["value"]
        context.user_data["original_exclusion_message"] = exclusion["message"]

        await update.message.reply_text(
            f"✏️ Editing Exclusion ID: `{exclusion_no}`\n"
            f"Current Value: `{exclusion['value']}`\n"
            f"Current Message: `{exclusion['message']}`\n\n" 
            "Please send the **new value** for this exclusion. (Cost: 5 ZC)",
            parse_mode='Markdown'
        )
        context.user_data["user_action"] = "edit_exclusion_value"
        return EDIT_USER_EXCLUSION_VALUE

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ID. Please send a number.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_edit_exclusion_select", "style": "primary"}],
                [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
            ])
        )
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

async def handle_edit_user_exclusion_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the new exclusion value."""
    user_id = update.message.from_user.id
    new_value = update.message.text.strip()
    exclusion_no = context.user_data.get("edit_exclusion_no")

    if not exclusion_no:
        await update.message.reply_text("❌ Error: Exclusion ID not found. Please start over.",
                                        reply_markup=create_keyboard([
                                            [{"text": "✏️ Edit Exclusion", "callback_data": "user_edit_exclusion_select", "style": "primary"}]
                                        ]))
        context.user_data.pop("user_action", None)
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
                    [{"text": "↩️ Try Again", "callback_data": "user_edit_exclusion_select", "style": "primary"}],
                    [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
                ])
            )
            context.user_data.pop("user_action", None)
            return ConversationHandler.END

    context.user_data["new_exclusion_value"] = new_value
    await update.message.reply_text(
        f"Got it! New value will be: `{new_value}`\n\n" 
        "Now, please send the **new message** for this exclusion.",
        parse_mode='Markdown'
    )
    context.user_data["user_action"] = "edit_exclusion_message"
    return EDIT_USER_EXCLUSION_MESSAGE

async def handle_edit_user_exclusion_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for the new exclusion message and update the exclusion."""
    user_id = update.message.from_user.id
    new_message = update.message.text.strip()
    exclusion_no = context.user_data.get("edit_exclusion_no")
    new_value = context.user_data.get("new_exclusion_value")
    original_value = context.user_data.get("original_exclusion_value")
    original_message = context.user_data.get("original_exclusion_message")

    if not exclusion_no or not new_value:
        await update.message.reply_text("❌ Error: Exclusion ID or new value not found. Please start over.",
                                        reply_markup=create_keyboard([
                                            [{"text": "✏️ Edit Exclusion", "callback_data": "user_edit_exclusion_select", "style": "primary"}]
                                        ]))
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

    # Check if any changes were actually made
    if new_value.lower() == original_value.lower() and new_message == original_message:
        await update.message.reply_text(
            f"ℹ️ No changes detected for Exclusion ID `{exclusion_no}`. No ZC deducted.",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "👀 View My Exclusions", "callback_data": "user_view_exclusions", "style": "info"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        context.user_data.pop("edit_exclusion_no", None)
        context.user_data.pop("new_exclusion_value", None)
        context.user_data.pop("original_exclusion_value", None)
        context.user_data.pop("original_exclusion_message", None)
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

    # Deduct 5 ZC for editing
    edit_cost = 5
    user_credits = await UserManager.get_user_credits(user_id)
    if user_credits < edit_cost:
        await update.message.reply_text(
            f"❌ Insufficient ZC to edit this exclusion. You need {edit_cost} ZC.",
            reply_markup=create_keyboard([
                [{"text": "💳 Buy ZC Packs", "callback_data": "shop_category_zc", "style": "success"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        context.user_data.pop("user_action", None)
        return ConversationHandler.END
    
    await UserManager.deduct_credits_raw(user_id, edit_cost)

    success = await ExclusionManager.update_exclusion(
        exclusion_no=exclusion_no,
        new_value=new_value,
        new_message=new_message,
        user_id=user_id,
        is_admin=False
    )

    if success:
        await update.message.reply_text(
            f"✅ Exclusion ID `{exclusion_no}` updated successfully for {edit_cost} ZC!\n\n" 
            f"New Value: `{new_value}`\n"
            f"New Message: `{new_message}`",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "👀 View My Exclusions", "callback_data": "user_view_exclusions", "style": "info"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update exclusion. An error occurred or the value might be a duplicate.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_edit_exclusion_select", "style": "primary"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    
    context.user_data.pop("edit_exclusion_no", None)
    context.user_data.pop("new_exclusion_value", None)
    context.user_data.pop("original_exclusion_value", None)
    context.user_data.pop("original_exclusion_message", None)
    context.user_data.pop("user_action", None)
    return ConversationHandler.END

async def delete_user_exclusion_select(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt user to select an exclusion to delete."""
    user_id = query.from_user.id
    user_exclusions = await ExclusionManager.get_user_exclusions(user_id)
    
    if not user_exclusions:
        await query.edit_message_text(
            text="❌ You have no exclusion slots to delete.",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        return ConversationHandler.END

    buttons = [[{"text": f"ID: {ex['exclusion_no']} - {ex['value']}", "callback_data": f"user_select_delete_slot_{ex['exclusion_no']}", "style": "info"}] for ex in user_exclusions]
    buttons.append([{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}])

    await query.edit_message_text(
        text="🗑️ DELETE EXCLUSION\n\n" 
             "Please select the `ID` of the exclusion you want to delete, or send the ID directly.",
        parse_mode='Markdown',
        reply_markup=create_keyboard(buttons)
    )
    context.user_data["user_action"] = "delete_exclusion_select"
    return DELETE_USER_EXCLUSION_CONFIRM

async def handle_delete_user_exclusion_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for selecting an exclusion to delete and ask for confirmation."""
    user_id = update.message.from_user.id
    try:
        exclusion_no = int(update.message.text.strip())
        exclusion = await ExclusionManager.get_exclusion_by_id(exclusion_no)

        if not exclusion or exclusion.get("slot_owner") != user_id:
            await update.message.reply_text(
                f"❌ Exclusion with ID `{exclusion_no}` not found or not owned by you. Please try again or cancel.",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": "user_delete_exclusion_select", "style": "primary"}],
                    [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
                ])
            )
            context.user_data.pop("user_action", None)
            return ConversationHandler.END
        
        context.user_data["delete_exclusion_no"] = exclusion_no

        await update.message.reply_text(
            f"🗑️ Confirm Deletion\n\n" 
            f"Are you sure you want to delete exclusion ID `{exclusion_no}`?\n"
            f"Value: `{exclusion.get('value', 'N/A')}`\n"
            f"Message: `{exclusion.get('message', 'N/A')}`",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "✅ Yes, Delete", "callback_data": f"user_delete_exclusion_confirm_{exclusion_no}", "style": "danger"}],
                [{"text": "❌ No, Cancel", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ID. Please send a number.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_delete_exclusion_select", "style": "primary"}],
                [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
            ])
        )
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

async def delete_user_exclusion_confirmed(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete the exclusion after confirmation."""
    user_id = query.from_user.id
    parts = query.data.split('_')
    exclusion_no = int(parts[-1])

    success = await ExclusionManager.delete_exclusion(exclusion_no=exclusion_no, user_id=user_id, is_admin=False)

    if success:
        await query.edit_message_text(
            f"✅ Exclusion ID `{exclusion_no}` deleted successfully! The slot is now free.",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "👀 View My Exclusions", "callback_data": "user_view_exclusions", "style": "info"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ Failed to delete exclusion. It might not exist or not be owned by you.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_delete_exclusion_select", "style": "primary"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    
    context.user_data.pop("delete_exclusion_no", None)

async def clear_user_exclusion_slot_select(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt user to select an exclusion slot to clear."""
    user_id = query.from_user.id
    user_exclusions = await ExclusionManager.get_user_exclusions(user_id)
    filled_exclusions = [ex for ex in user_exclusions if not ex.get("is_placeholder", True)]

    if not filled_exclusions:
        await query.edit_message_text(
            text="❌ You have no filled exclusion slots to clear.",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        return ConversationHandler.END

    buttons = [[{"text": f"ID: {ex['exclusion_no']} - {ex['value']}", "callback_data": f"user_select_clear_slot_{ex['exclusion_no']}", "style": "info"}] for ex in filled_exclusions]
    buttons.append([{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}])

    await query.edit_message_text(
        text="🔄 CLEAR EXCLUSION SLOT\n\n" 
             "Please select the `ID` of the exclusion slot you want to clear (this will make it empty, but you keep the slot).",
        parse_mode='Markdown',
        reply_markup=create_keyboard(buttons)
    )
    context.user_data["user_action"] = "clear_exclusion_slot_select"
    return CLEAR_USER_EXCLUSION_CONFIRM

async def handle_clear_user_exclusion_slot_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the input for selecting an exclusion slot to clear and ask for confirmation."""
    user_id = update.message.from_user.id
    try:
        exclusion_no = int(update.message.text.strip())
        exclusion = await ExclusionManager.get_exclusion_by_id(exclusion_no)

        if not exclusion or exclusion.get("slot_owner") != user_id or exclusion.get("is_placeholder", True):
            await update.message.reply_text(
                f"❌ Exclusion with ID `{exclusion_no}` not found, not owned by you, or is already empty. Please try again or cancel.",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": "user_clear_exclusion_slot_select", "style": "primary"}],
                    [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
                ])
            )
            context.user_data.pop("user_action", None)
            return ConversationHandler.END
        
        context.user_data["clear_exclusion_no"] = exclusion_no

        await update.message.reply_text(
            f"🔄 Confirm Clear Slot\n\n" 
            f"Are you sure you want to clear exclusion slot `{exclusion_no}`?\n"
            f"Value: `{exclusion.get('value', 'N/A')}`\n"
            f"Message: `{exclusion.get('message', 'N/A')}`\n\n" 
            "This will make the slot empty, but you will retain ownership and can fill it again without paying.",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "✅ Yes, Clear Slot", "callback_data": f"user_clear_exclusion_slot_confirm_{exclusion_no}", "style": "danger"}],
                [{"text": "❌ No, Cancel", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid ID. Please send a number.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_clear_exclusion_slot_select", "style": "primary"}],
                [{"text": "🚫 Cancel", "callback_data": "user_exclusion_management", "style": "danger"}]
            ])
        )
        context.user_data.pop("user_action", None)
        return ConversationHandler.END

async def clear_user_exclusion_slot_confirmed(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the exclusion slot after confirmation."""
    user_id = query.from_user.id
    parts = query.data.split('_')
    exclusion_no = int(parts[-1])

    # To clear a slot, we update it to be a placeholder again with empty value/message
    success = await ExclusionManager.update_exclusion(
        exclusion_no=exclusion_no,
        new_value="",
        new_message="",
        user_id=user_id,
        is_admin=False # User is clearing their own slot
    )
    # Manually set it as a placeholder
    db = await DatabaseManager.load_db()
    if str(exclusion_no) in db.get("exclusions", {}):
        db["exclusions"][str(exclusion_no)]["is_placeholder"] = True
        await DatabaseManager.save_db(db)
        success = True # Ensure success if we manually set placeholder

    if success:
        await query.edit_message_text(
            f"✅ Exclusion slot `{exclusion_no}` cleared successfully! You can now fill it with a new query.",
            parse_mode='Markdown',
            reply_markup=create_keyboard([
                [{"text": "📝 Fill Empty Slot", "callback_data": "user_fill_exclusion_slot", "style": "success"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    else:
        await query.edit_message_text(
            "❌ Failed to clear exclusion slot. It might not exist or not be owned by you.",
            reply_markup=create_keyboard([
                [{"text": "↩️ Try Again", "callback_data": "user_clear_exclusion_slot_select", "style": "primary"}],
                [{"text": "🔙 Back to Exclusion Management", "callback_data": "user_exclusion_management", "style": "secondary"}]
            ])
        )
    
    context.user_data.pop("clear_exclusion_no", None)

user_exclusion_management_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(fill_exclusion_slot_start, pattern="^user_fill_exclusion_slot$"),
        CallbackQueryHandler(edit_user_exclusion_select, pattern="^user_edit_exclusion_select$"),
        CallbackQueryHandler(delete_user_exclusion_select, pattern="^user_delete_exclusion_select$"),
        CallbackQueryHandler(clear_user_exclusion_slot_select, pattern="^user_clear_exclusion_slot_select$"),
    ],
    states={
        FILL_EXCLUSION_VALUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fill_exclusion_value),
            CallbackQueryHandler(handle_select_fill_slot, pattern="^user_select_fill_slot_")
        ],
        FILL_EXCLUSION_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fill_exclusion_message)],
        EDIT_USER_EXCLUSION_SELECT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_user_exclusion_select),
            CallbackQueryHandler(lambda q, c: handle_edit_user_exclusion_select(Update(update_id=q.update_id, callback_query=q), c), pattern="^user_select_edit_slot_")
        ],
        EDIT_USER_EXCLUSION_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_user_exclusion_value)],
        EDIT_USER_EXCLUSION_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_user_exclusion_message)],
        DELETE_USER_EXCLUSION_CONFIRM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_delete_user_exclusion_select),
            CallbackQueryHandler(lambda q, c: handle_delete_user_exclusion_select(Update(update_id=q.update_id, callback_query=q), c), pattern="^user_select_delete_slot_")
        ],
        CLEAR_USER_EXCLUSION_CONFIRM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clear_user_exclusion_slot_select),
            CallbackQueryHandler(lambda q, c: handle_clear_user_exclusion_slot_select(Update(update_id=q.update_id, callback_query=q), c), pattern="^user_select_clear_slot_")
        ],
    },
    fallbacks=[
        CallbackQueryHandler(show_user_exclusion_management_panel, pattern="^user_exclusion_management$"),
        CallbackQueryHandler(lambda q, c: ConversationHandler.END, pattern="^back_to_menu$"),
    ],
    map_to_parent={
        ConversationHandler.END: "user_dashboard" # Or wherever the user should return
    },
    per_message=True,
)
