from telegram.ext import ContextTypes
from ...database.db_users import UserManager
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...config import BOT_NAME, logger

async def show_refer_earn(query, context):
    """Show referral program information"""
    user_id = query.from_user.id
    user = await UserManager.get_user(user_id)
    
    if not user:
        await query.edit_message_text(text="❌ User not found.")
        return

    db = await DatabaseManager.load_db()
    referral_bonus = db["settings"].get("referral_bonus", 0.5)
    
    # Get bot username from context
    try:
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
    except Exception as e:
        logger.error(f"Error getting bot info: {e}")
        referral_link = "Unable to generate referral link"
    
    await query.edit_message_message(
        text="🎁 Refer & Earn\n\n" 
             f"Invite friends to join {BOT_NAME} and earn {referral_bonus} credits for each referral!\n\n" 
             f"Your referral link:\n`{referral_link}`\n\n" 
             f"👥 Total Referrals: {len(user.get('referrals', []))}\n" 
             f"💎 Earned Credits: {len(user.get('referrals', [])) * referral_bonus}",
        parse_mode='Markdown',
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"}]
        ])
    )

async def refer_command(update, context):
    """Handle /refer command"""
    # This function will be called from the main bot file, so it needs to import check_force_join
    from ...utils.join_checker import check_force_join
    if not await check_force_join(update, context):
        return
    
    class MockQuery:
        def __init__(self, user, message):
            self.from_user = user
            self.message = message
            
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    
    mock_query = MockQuery(update.effective_user, update.message)
    await show_refer_earn(mock_query, context)