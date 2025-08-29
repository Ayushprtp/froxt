from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ...database.db_users import UserManager
from ...utils.keyboards import create_keyboard
from ...utils.join_checker import check_force_join
from ...config import BOT_NAME, ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_force_join(update, context):
        return

    user = update.effective_user
    args = context.args
    referrer_id = int(args[0]) if args and args[0].isdigit() else None

    user_data = await UserManager.create_user(user.id, user.username, referrer_id)
    
    is_new_user = datetime.now() - datetime.fromisoformat(user_data["joined_at"]) < timedelta(minutes=1)
    
    menu_buttons = [
        [
            {"text": "🛠️ OSINT Tools", "callback_data": "osint_tools", "style": "premium"},
            {"text": "📊 My Dashboard", "callback_data": "my_dashboard", "style": "info"},
        ],
        [
            {"text": "🎁 Refer & Earn", "callback_data": "refer_earn", "style": "success"},
            {"text": "💳 Buy Credits", "callback_data": "buy_credits", "style": "warning"},
        ],
        [
            {"text": "📞 Help & Support", "callback_data": "contact_support", "style": "info"},
            {"text": "📢 News & Updates", "callback_data": "news_updates", "style": "secondary"},
        ]
    ]

    if user.id in ADMIN_IDS:
        menu_buttons.append([
            {"text": "👑 Admin Panel", "callback_data": "admin_panel", "style": "danger"}
        ])

    welcome_text = "🔙 Welcome Back!" if not is_new_user else f"🎉 Welcome to {BOT_NAME}"
    bonus_text = f"\n💎 Welcome Bonus: +{user_data['credits']} credits" if is_new_user else ""
    
    stats_text = f"\n📈 Your Stats:\n• Total Requests: {user_data.get('total_requests', 0)}\n• Member Since: {datetime.fromisoformat(user_data['joined_at']).strftime('%B %Y')}"
    
    welcome_message = (
        f"{welcome_text}\n\n"
        f"👋 Hello {user.full_name or 'User'}{bonus_text}\n\n"
        f"💎 Credits: {user_data['credits']}\n"
        f"👥 Referrals: {len(user_data.get('referrals', []))}{stats_text}\n\n"
        f"🔍 Powerful OSINT tools at your fingertips:\n"
        f"• 📱 Mobile & Email Lookup\n"
        f"• 🌐 Social Media Investigation\n"
        f"• 🚗 Vehicle & Identity Search\n"
        f"• 🔬 Deep Mobile Analysis (NEW!)\n"
        f"• 📊 Advanced Analytics\n\n"
        f"⬇️ Choose an option below to continue:"
    )

    if update.message:
        await update.message.reply_text(
            welcome_message,
            reply_markup=create_keyboard(menu_buttons)
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_message,
            reply_markup=create_keyboard(menu_buttons)
        )