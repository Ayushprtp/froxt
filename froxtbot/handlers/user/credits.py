from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_users import UserManager
from ...database.db_management import DatabaseManager
from ...config.services import SERVICES_CONFIG
from ...utils.keyboards import create_keyboard

async def credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /credits command"""
    # This function will be called from the main bot file, so it needs to import check_force_join
    from ...utils.join_checker import check_force_join
    if not await check_force_join(update, context):
        return
    
    user_id = update.effective_user.id
    user = await UserManager.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ User not found. Please use /start first.")
        return
    
    # Build credit costs dictionary from SERVICES_CONFIG
    credit_costs = {tool: service_info["servicecost"] for tool, service_info in SERVICES_CONFIG.items()}
    paid_tools = [tool for tool, cost in credit_costs.items() if cost > 0]
    
    credits_text = (
        f"💎 Your Credits\n\n"
        f"Current Balance: {user['credits']} credits\n"
        f"Total Requests: {user.get('total_requests', 0)}\n\n"
        f"💰 Premium Tools:\n"
    )
    
    if paid_tools:
        for tool in paid_tools:
            cost = credit_costs[tool]
            tool_name = tool.replace('_', ' ').title()
            credits_text += f"• {tool_name}: {cost} credits\n"
    else:
        credits_text += "• All tools are currently free!"
    
    credits_text += "\n🆓 Most tools are completely free to use!"
    
    await update.message.reply_text(
        credits_text,
        reply_markup=create_keyboard([
            [{"text": "💳 Buy More Credits", "callback_data": "buy_credits", "style": "success"}],
            [{"text": "🎁 Refer Friends", "callback_data": "refer_earn", "style": "info"}]
        ])
    )