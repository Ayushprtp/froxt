from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_management import DatabaseManager
from ...utils.ui import UIElements
from ...utils.join_checker import check_force_join

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command"""
    if not await check_force_join(update, context):
        return
    
    db = await DatabaseManager.load_db()
    stats = db.get("stats", {})
    
    total_users = len(db["users"])
    total_requests = stats.get("total_requests", 0)
    success_rate = (stats.get('successful_requests', 0) / max(total_requests, 1)) * 100
    
    stats_text = (
        "📊 Bot Statistics\n\n"
        f"👥 Total Users: {UIElements.format_number(total_users)}\n"
        f"📈 Total Requests: {UIElements.format_number(total_requests)}\n"
        f"✅ Success Rate: {success_rate:.1f}%\n"
        f"💎 Credits Distributed: {UIElements.format_number(stats.get('total_credits_distributed', 0))}"
        f"🏆 Peak Users: {stats.get('peak_users', 0)}\n\n"
        f"🤖 Bot Version: 2.2\n"
        f"🔬 New: Deep Mobile Scan\n"
        f"📄 Enhanced: Pagination Support\n"
        f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    
    await update.message.reply_text(stats_text)