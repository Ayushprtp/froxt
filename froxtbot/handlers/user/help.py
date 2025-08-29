from telegram import Update
from telegram.ext import ContextTypes
from ...config import BOT_NAME
from ...utils.keyboards import create_keyboard
from ...utils.join_checker import check_force_join

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    if not await check_force_join(update, context):
        return
    
    help_text = (
        f"📚 {BOT_NAME} Help\n\n"
        "🔧 Available Commands:\n"
        "• /start - Start the bot\n"
        "• /dashboard - View your dashboard\n"
        "• /tools - Access OSINT tools\n"
        "• /credits - Check your credits\n"
        "• /refer - Get referral link\n"
        "• /buy - Buy credits\n"
        "• /support - Contact support\n"
        "• /help - Show this help\n\n"
        "🛠️ Available Tools:\n"
        "• 📱 Mobile Lookup (FREE)\n"
        "• 📧 Email Search (FREE)\n"
        "• 🆔 Aadhar Lookup (FREE)\n"
        "• 💰 UPI Services (FREE)\n"
        "• 🌐 IP & Username Scanning (FREE)\n"
        "• 🚗 Vehicle Information (FREE)\n"
        "• 🍞 Ration Card Info (FREE)\n"
        "• 🔓 Breach Checking (FREE)\n"
        "• 🔍 Full OSINT Scan (FREE)\n"
        "• 🔬 Deep Mobile Scan (5 credits)\n\n"
        "💡 Most tools are completely free!\n"
        "🔍 Advanced pagination for large results\n"
        "📄 File export for comprehensive data"
    )
    
    await update.message.reply_text(
        help_text,
        reply_markup=create_keyboard([
            [{"text": "🛠️ Open Tools", "callback_data": "osint_tools", "style": "primary"}],
            [{"text": "🏠 Main Menu", "callback_data": "back_to_menu", "style": "secondary"}]
        ])
    )