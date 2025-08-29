from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_users import UserManager
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...utils.ui import UIElements

async def show_user_dashboard(query) -> None:
    user_id = query.from_user.id
    user = await UserManager.get_user(user_id)

    if not user:
        await query.edit_message_text(text="❌ User not found.")
        return

    db = await DatabaseManager.load_db()
    
    join_date = datetime.fromisoformat(user['joined_at'])
    days_since_join = max((datetime.now() - join_date).days, 1)
    avg_requests_per_day = user.get('total_requests', 0) / days_since_join

    dashboard_menu = [
        [
            {"text": "💳 Buy Credits", "callback_data": "buy_credits", "style": "success"},
            {"text": "🎁 Refer Friends", "callback_data": "refer_earn", "style": "info"},
        ],
        [
            {"text": "📊 Usage History", "callback_data": "usage_history", "style": "info"},
            {"text": "🏆 Achievements", "callback_data": "achievements", "style": "premium"},
        ],
        [
            {"text": "🚫 My Exclusions", "callback_data": "user_exclusion_management", "style": "danger"},
        ],
        [
            {"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"},
        ]
    ]

    dashboard_text = (
        "📊 Your Dashboard\n\n"
        f"💎 Credits Balance: {user['credits']}\n"
        f"📈 Total Requests: {UIElements.format_number(user.get('total_requests', 0))}\n"
        f"📅 Daily Requests: {user.get('daily_requests', 0)}\n"
        f"👥 Referrals: {len(user.get('referrals', []))}\n\n"
        "📈 Statistics:\n"
        f"• 📅 Member since: {join_date.strftime('%B %d, %Y')}\n"
        f"• ⏳ Days active: {days_since_join}\n"
        f"• 📊 Avg requests/day: {avg_requests_per_day:.1f}\n"
        f"• 🎫 Tier: {user.get('subscription_tier', 'Free').title()}\n\n"
        "💡 Tip: Refer friends to earn bonus credits!"
    )

    await query.edit_message_text(
        text=dashboard_text,
        reply_markup=create_keyboard(dashboard_menu)
    )

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dashboard command"""
    # This function will be called from the main bot file, so it needs to import check_force_join
    from ...utils.join_checker import check_force_join
    if not await check_force_join(update, context):
        return
    
    user_id = update.effective_user.id
    user = await UserManager.get_user(user_id)
    
    if not user:
        await UserManager.create_user(user_id, update.effective_user.username)
        user = await UserManager.get_user(user_id)
    
    # Create a mock callback query for dashboard function
    class MockQuery:
        def __init__(self, user, message):
            self.from_user = user
            self.message = message
            
        async def edit_message_text(self, text, reply_markup=None):
            await self.message.reply_text(text, reply_markup=reply_markup)
    
    mock_query = MockQuery(update.effective_user, update.message)
    await show_user_dashboard(mock_query)