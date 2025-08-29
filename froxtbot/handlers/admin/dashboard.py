from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...config import ADMIN_IDS

async def show_admin_panel(query) -> None:
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return

    db = await DatabaseManager.load_db()
    stats = db.get('stats', {})
    
    total_users = len(db["users"])
    active_users = sum(1 for user in db["users"].values() if not user.get("banned", False))
    banned_users = total_users - active_users
    total_credits = sum(user["credits"] for user in db["users"].values())
    
    # Enhanced admin menu
    admin_menu = [
        [
            {"text": "👥 User Management", "callback_data": "admin_users", "style": "info"},
            {"text": "💎 Credit Management", "callback_data": "admin_credits", "style": "premium"},
        ],
        [
            {"text": "📊 Analytics", "callback_data": "admin_analytics", "style": "success"},
            {"text": "⚙️ System Settings", "callback_data": "admin_settings", "style": "warning"},
        ],
        [
            {"text": "📢 Broadcast", "callback_data": "broadcast_new", "style": "danger"}, # Changed to broadcast_new to start conversation
            {"text": "💾 Export Data", "callback_data": "admin_export", "style": "info"},
        ],
        [
            {"text": "🛡️ Security Center", "callback_data": "admin_security_center", "style": "warning"},
            {"text": "🔧 Maintenance", "callback_data": "admin_maintenance", "style": "warning"},
        ],
        [
            {"text": "🔌 API Configuration", "callback_data": "admin_api_config", "style": "info"},
            {"text": "🚫 Exclusion Management", "callback_data": "admin_exclusion_management", "style": "danger"},
        ],
        [
            {"text": " History Management", "callback_data": "admin_history_management", "style": "info"},
        ],
        [
            {"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"},
        ]
    ]

    success_rate = (stats.get('successful_requests', 0) / max(stats.get('total_requests', 1), 1)) * 100

    admin_text = (
        "👑 ADMIN DASHBOARD\n\n"
        "📊 System Statistics:\n"
        f"• 👥 Total Users: {total_users}\n"
        f"• ✅ Active Users: {active_users}\n"
        f"• 🚫 Banned Users: {banned_users}\n"
        f"• 💎 Total Credits: {total_credits}\n"
        f"• 📈 Success Rate: {success_rate:.1f}%\n\n"
        "🎯 Admin Features:\n"
        "• 👥 Complete User Management\n"
        "• 💰 Credit Control System\n"
        "• 📊 Live Analytics Dashboard\n"
        "• ⚙️ Full System Configuration\n"
        "• 🛡️ Security & Monitoring\n"
        "• 🔧 Maintenance Tools\n"
        "• 🔌 API Configuration\n\n"
        f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    await query.edit_message_text(
        text=admin_text,
        reply_markup=create_keyboard(admin_menu)
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command"""
    # This function will be called from the main bot file, so it needs to import check_force_join
    from ...utils.join_checker import check_force_join
    if not await check_force_join(update, context):
        return
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You don't have admin permissions.")
        return
    
    class MockQuery:
        def __init__(self, user, message):
            self.from_user = user
            self.message = message
            
        async def edit_message_text(self, text, reply_markup=None):
            await self.message.reply_text(text, reply_markup=reply_markup)
    
    mock_query = MockQuery(update.effective_user, update.message)
    await show_admin_panel(mock_query)