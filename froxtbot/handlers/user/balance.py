from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_users import UserManager
from ...utils.join_checker import check_force_join

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /balance command - shows user's account balance"""
    if not await check_force_join(update, context):
        return
    
    user_id = update.effective_user.id
    user = await UserManager.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ User not found. Please use /start first.")
        return
    
    balance_text = (
        f"💰 Your Account Balance\n\n"
        f"💎 Credits: {user['credits']}\n"
        f"👥 Referrals: {len(user.get('referrals', []))}\n"
        f"📈 Total Requests: {user.get('total_requests', 0)}"
    )
    
    await update.message.reply_text(balance_text)