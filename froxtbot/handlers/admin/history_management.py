import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_history import get_all_query_history
from ...database.db_management import DatabaseManager
from ...database.db_users import UserManager
from ...utils.keyboards import create_keyboard, create_pagination_keyboard
from ...utils.pagination import PaginationManager
from ...config import ADMIN_IDS, DEFAULT_API_CONFIG

logger = logging.getLogger(__name__)

async def show_history_management_panel(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the admin history management panel."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return

    admin_menu = [
        [
            {"text": "👀 View All Queries", "callback_data": "admin_view_all_queries", "style": "info"},
            {"text": "🔍 Search Queries", "callback_data": "admin_search_queries", "style": "primary"},
        ],
        [
            {"text": "🔙 Back to Admin Panel", "callback_data": "admin_panel", "style": "secondary"},
        ]
    ]

    await query.edit_message_text(
        text="📜 HISTORY MANAGEMENT\n\n"
             "Here you can view and manage the bot's query history.",
        reply_markup=create_keyboard(admin_menu)
    )

async def view_all_queries(query, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
    """Display a paginated list of all queries."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return

    db = await DatabaseManager.load_db()
    page_size = DEFAULT_API_CONFIG["PAGINATION_SIZE"]
    
    all_queries, total_items = await get_all_query_history(page=page, limit=page_size)

    if not all_queries:
        await query.edit_message_text(
            text="🚫 No queries found in the database.",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to History Management", "callback_data": "admin_history_management", "style": "secondary"}]
            ])
        )
        return

    message_text = "📜 ALL QUERY HISTORY\n\n"
    for q in all_queries:
        user = await UserManager.get_user(q['user_id'])
        username = user.get('username', f"User {q['user_id']}") if user else f"User {q['user_id']}"
        timestamp = datetime.fromisoformat(q['timestamp']).strftime('%Y-%m-%d %H:%M')
        message_text += (
            f"• User: `{username}` (ID: `{q['user_id']}`)\n"
            f"  Service: `{q['service_name']}`\n"
            f"  Query: `{q['query_text']}`\n"
            f"  Time: `{timestamp}`\n"
            f"-----------------------------------\n"
        )
    
    total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
    message_text += f"📄 Page {page}/{total_pages}\n"
    message_text += f"📊 Total Queries: {total_items}\n\n"

    pagination_buttons = create_pagination_keyboard(
        page,
        total_pages,
        "admin_view_all_queries_page"
    )
    
    final_keyboard = pagination_buttons + [
        [{"text": "🔙 Back to History Management", "callback_data": "admin_history_management", "style": "secondary"}]
    ]

    await query.edit_message_text(
        text=message_text,
        parse_mode='Markdown',
        reply_markup=create_keyboard(final_keyboard)
    )

async def handle_all_queries_pagination(query, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle pagination for viewing all queries."""
    parts = callback_data.split('_')
    page = int(parts[-1])
    await view_all_queries(query, context, page)

# Placeholder for search queries functionality (can be expanded later)
async def search_queries(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Placeholder for searching queries."""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return
    
    await query.edit_message_text(
        text="🔍 SEARCH QUERIES\n\n"
             "This feature is under development. You will be able to search queries by user ID, service name, or time period.",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to History Management", "callback_data": "admin_history_management", "style": "secondary"}]
        ])
    )
