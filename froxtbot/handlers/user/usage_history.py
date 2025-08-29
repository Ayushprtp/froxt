from datetime import datetime
from ...database.db_users import UserManager
from ...database.db_history import get_user_query_history
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard, create_pagination_keyboard
from ...utils.pagination import PaginationManager
from ...config import DEFAULT_API_CONFIG

async def show_usage_history(query, context, page: int = 1):
    """Show user's usage history including queries."""
    user_id = query.from_user.id
    user = await UserManager.get_user(user_id)
    
    if not user:
        await query.edit_message_text(text="❌ User not found.")
        return

    # Fetch paginated query history
    db = await DatabaseManager.load_db()
    page_size = db["api_config"].get("PAGINATION_SIZE", DEFAULT_API_CONFIG["PAGINATION_SIZE"])
    
    query_history, total_items = await get_user_query_history(user_id, page=page, limit=page_size)

    history_text = (
        "📊 Your Usage History\n\n"
        f"• Total Requests: {user.get('total_requests', 0)}\n"
        f"• Today's Requests: {user.get('daily_requests', 0)}\n"
        f"• Last Active: {datetime.fromisoformat(user['last_active']).strftime('%Y-%m-%d %H:%M')}\n"
        f"• Member Since: {datetime.fromisoformat(user['joined_at']).strftime('%Y-%m-%d')}\n"
        f"• Referrals Made: {len(user.get('referrals', []))}\n\n"
        "--- Recent Queries ---\n"
    )

    if query_history:
        for entry in query_history:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
            history_text += f"• `{timestamp}`: {entry['service_name']} - `{entry['query_text']}`\n"
    else:
        history_text += "No recent queries.\n"

    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
    history_text += f"\n📄 Page {page}/{total_pages}\n"
    history_text += f"📊 Total Queries: {total_items}\n"

    pagination_buttons = create_pagination_keyboard(
        page,
        total_pages,
        "user_usage_history_page"
    )

    final_keyboard = pagination_buttons + [
        [{"text": "🔙 Back to Dashboard", "callback_data": "my_dashboard", "style": "secondary"}]
    ]

    await query.edit_message_text(
        text=history_text,
        parse_mode='Markdown',
        reply_markup=create_keyboard(final_keyboard)
    )

async def handle_usage_history_pagination(query, context, callback_data):
    """Handle pagination for user usage history."""
    parts = callback_data.split('_')
    page = int(parts[-1])
    await show_usage_history(query, context, page)
