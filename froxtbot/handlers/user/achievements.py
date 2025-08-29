from database.db_users import UserManager
from utils.keyboards import create_keyboard

async def show_achievements(query):
    """Show user achievements"""
    user_id = query.from_user.id
    user = await UserManager.get_user(user_id)
    
    if not user:
        await query.edit_message_text(text="❌ User not found.")
        return
    
    total_requests = user.get('total_requests', 0)
    referrals = len(user.get('referrals', []))
    
    achievements = []
    achievements.append("✅ New User: Joined the bot")
    
    if total_requests > 0:
        achievements.append("✅ First Request: Made your first OSINT query")
    else:
        achievements.append("⏳ First Request: Pending")
    
    if total_requests >= 10:
        achievements.append("✅ Active User: Made 10+ requests")
    else:
        achievements.append("⏳ Active User: Pending (10+ requests needed)")
    
    if total_requests >= 50:
        achievements.append("✅ Power User: Made 50+ requests")
    else:
        achievements.append("⏳ Power User: Pending (50+ requests needed)")
    
    if referrals > 0:
        achievements.append(f"✅ Referrer: Referred {referrals} users")
    else:
        achievements.append("⏳ Referrer: Pending (refer a friend)")

    achievement_text = "🏆 Your Achievements\n\n" + "\n".join(achievements)
    achievement_text += "\n\nKeep using the bot to unlock more achievements!"

    await query.edit_message_text(
        text=achievement_text,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Dashboard", "callback_data": "my_dashboard", "style": "secondary"}]
        ])
    )
