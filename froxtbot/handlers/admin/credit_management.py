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
from ...database.db_management import DatabaseManager
from ...database.db_users import UserManager
from ...utils.keyboards import create_keyboard, build_cancel_keyboard
from .dashboard import show_admin_panel as handle_admin_panel
from ...config import ADMIN_IDS, logger
from datetime import datetime

# Conversation states
(
    AWAIT_CREDIT_USER_ID,
    AWAIT_CREDIT_AMOUNT,
    AWAIT_GIVEAWAY_AMOUNT,
) = range(3)

async def handle_admin_credits(query):
    """Handle credit management"""
    credit_management_menu = [
        [
            {"text": "💰 Credit Stats", "callback_data": "admin_credit_stats", "style": "info"},
            {"text": "🏆 Top Credits", "callback_data": "admin_top_credits", "style": "premium"},
        ],
        [
            {"text": "➕ Add Credits", "callback_data": "admin_add_credits_start", "style": "success"},
            {"text": "➖ Remove Credits", "callback_data": "admin_remove_credits_start", "style": "warning"},
        ],
        [
            {"text": "🎁 Credit Giveaway", "callback_data": "admin_credit_giveaway_start", "style": "success"},
            {"text": "📊 Credit Analytics", "callback_data": "admin_credit_analytics", "style": "info"},
        ],
        [
            {"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"},
        ]
    ]

    await query.edit_message_text(
        text="💎 CREDIT MANAGEMENT\n\n"
             "Manage credit system and user balances:\n\n"
             "• 💰 Credit Stats: View credit statistics\n"
             "• 🏆 Top Credits: Users with most credits\n"
             "• ➕ Add Credits: Add credits to user\n"
             "• ➖ Remove Credits: Remove credits from user\n"
             "• 🎁 Credit Giveaway: Give credits to all users\n"
             "• 📊 Credit Analytics: Credit usage analytics",
        reply_markup=create_keyboard(credit_management_menu)
    )

async def handle_admin_credit_stats(query) -> None:
    db = await DatabaseManager.load_db()
    users = list(db["users"].values())
    
    total_credits = sum(u.get('credits', 0) for u in users)
    avg_credits = total_credits / max(len(users), 1)
    zero_credits = sum(1 for u in users if u.get('credits', 0) == 0)
    
    stats_text = (
        "💎 Credit Statistics\n\n"
        f"• 💰 Total Credits: {total_credits}\n"
        f"• 📊 Average per User: {avg_credits:.1f}\n"
        f"• ❌ Users with 0 Credits: {zero_credits}\n"
        f"• ✅ Users with Credits: {len(users) - zero_credits}\n"
        f"• 🎁 Total Distributed: {db['stats'].get('total_credits_distributed', 0)}"
    )
    
    await query.edit_message_text(
        text=stats_text,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Credits", "callback_data": "admin_credits", "style": "secondary"}]
        ])
    )

async def handle_admin_top_credits(query) -> None:
    db = await DatabaseManager.load_db()
    users = sorted(db["users"].values(), key=lambda x: x.get('credits', 0), reverse=True)[:10]
    
    if not users:
        top_list = "💎 No users found."
    else:
        top_list = "💎 Top Credit Holders:\n\n"
        for i, user in enumerate(users, 1):
            username = user.get("username", "N/A")
            credits = user.get("credits", 0)
            top_list += f"{i}. {username} - {credits} credits\n"
    
    await query.edit_message_text(
        text=top_list,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Credits", "callback_data": "admin_credits", "style": "secondary"}]
        ])
    )

async def prompt_credit_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts for user ID to add/remove credits."""
    query = update.callback_query
    await query.answer()
    action_type = query.data.split('_')[1] # 'add' or 'remove'
    context.user_data['credit_action_type'] = action_type
    keyboard = build_cancel_keyboard("admin_credits")
    await query.edit_message_text(
        f"Enter the user ID to {action_type} credits for:", reply_markup=keyboard
    )
    return AWAIT_CREDIT_USER_ID

async def handle_credit_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles user ID input and prompts for amount."""
    try:
        user_id = int(update.message.text)
        user = await UserManager.get_user(user_id)
        if not user:
            await update.message.reply_text("User not found. Please enter a valid user ID.")
            return AWAIT_CREDIT_USER_ID
        
        context.user_data['target_user_id'] = user_id
        action_type = context.user_data['credit_action_type']
        keyboard = build_cancel_keyboard("admin_credits")
        await update.message.reply_text(
            f"Enter the amount of credits to {action_type} for user {user_id}:", reply_markup=keyboard
        )
        return AWAIT_CREDIT_AMOUNT
    except ValueError:
        await update.message.reply_text("Invalid user ID. Please enter a valid integer.")
        return AWAIT_CREDIT_USER_ID

async def handle_credit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles credit amount and updates user balance."""
    try:
        amount = float(update.message.text)
        user_id = context.user_data['target_user_id']
        action_type = context.user_data['credit_action_type']

        current_user = await UserManager.get_user(user_id)
        if not current_user:
            await update.message.reply_text("User not found. Operation cancelled.")
            context.user_data.clear()
            return ConversationHandler.END

        if action_type == "remove":
            amount = -amount # Make amount negative for removal

        success = await UserManager.update_user_credits(user_id, amount, f"admin_{action_type}_credits")
        if success:
            # Log the admin action to history
            db = await DatabaseManager.load_db()
            db.setdefault("admin_actions", []).append({
                "admin_user_id": update.effective_user.id,
                "action": f"{action_type}_credits_{abs(amount)}",
                "target_user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            await DatabaseManager.save_db(db)
            await update.message.reply_text(f"✅ Credits {action_type}ed successfully for user {user_id}.")
        else:
            await update.message.reply_text("❌ Failed to update credits. Check balance or try again.")
        
        context.user_data.clear()
        await handle_admin_panel(update.message) # Go back to admin dashboard
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a valid number.")
        return AWAIT_CREDIT_AMOUNT

async def prompt_credit_giveaway_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompts for the amount of credits to give away."""
    query = update.callback_query
    await query.answer()
    keyboard = build_cancel_keyboard("admin_credits")
    await query.edit_message_text(
        "Enter the amount of credits to give to ALL users:", reply_markup=keyboard
    )
    return AWAIT_GIVEAWAY_AMOUNT

async def handle_credit_giveaway_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the giveaway amount and distributes credits to all users."""
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("Amount must be positive. Please enter a valid number.")
            return AWAIT_GIVEAWAY_AMOUNT

        db = await DatabaseManager.load_db()
        users = list(db["users"].keys())
        
        success_count = 0
        for user_id_str in users:
            user_id = int(user_id_str)
            success = await UserManager.update_user_credits(user_id, amount, "admin_giveaway")
            if success:
                success_count += 1
        
        # Log the admin action to history
        db = await DatabaseManager.load_db()
        db.setdefault("admin_actions", []).append({
            "admin_user_id": update.effective_user.id,
            "action": f"credit_giveaway_{amount}",
            "details": {"successful_users": success_count, "total_users": len(users)},
            "timestamp": datetime.now().isoformat()
        })
        await DatabaseManager.save_db(db)
        await update.message.reply_text(f"✅ Credit giveaway complete! {success_count} users received {amount} credits.")
        
        context.user_data.clear()
        await handle_admin_panel(update.message) # Go back to admin dashboard
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Invalid amount. Please enter a valid number.")
        return AWAIT_GIVEAWAY_AMOUNT

async def end_credit_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ends the conversation and returns to the credit management menu."""
    query = update.callback_query
    if query:
        await query.answer()
        await handle_admin_credits(query)
    else:
        # If it's a message, reply and then go back to admin credits
        await update.message.reply_text("Operation cancelled.")
        # Create a mock query to call handle_admin_credits
        class MockQuery:
            def __init__(self, user, message):
                self.from_user = user
                self.message = message
            async def edit_message_text(self, text, reply_markup=None):
                await self.message.reply_text(text, reply_markup=reply_markup)
            async def answer(self, text=None, show_alert=False):
                pass
        mock_query = MockQuery(update.effective_user, update.message)
        await handle_admin_credits(mock_query)

    context.user_data.clear()
    return ConversationHandler.END


credit_management_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(prompt_credit_user_id, pattern="^admin_(add|remove)_credits_start$"),
        CallbackQueryHandler(prompt_credit_giveaway_amount, pattern="^admin_credit_giveaway_start$"),
    ],
    states={
        AWAIT_CREDIT_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), handle_credit_user_id)],
        AWAIT_CREDIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), handle_credit_amount)],
        AWAIT_GIVEAWAY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS), handle_credit_giveaway_amount)],
    },
    fallbacks=[
        CallbackQueryHandler(end_credit_conversation, pattern="^admin_credits$"),
        CommandHandler("cancel", end_credit_conversation),
        CommandHandler("start", end_credit_conversation),
    ],
    map_to_parent={ConversationHandler.END: -1},
)
