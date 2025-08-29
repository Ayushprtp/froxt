from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any
from .ui import UIElements

def create_button(text: str, callback_data: str = None, url: str = None, style: str = "primary") -> InlineKeyboardButton:
    prefix = UIElements.BUTTON_STYLES.get(style, "")
    button_text = f"{prefix}{text}"
    
    if url:
        return InlineKeyboardButton(button_text, url=url)
    else:
        return InlineKeyboardButton(button_text, callback_data=callback_data)

def create_keyboard(buttons: List[List[Dict]]) -> InlineKeyboardMarkup:
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for btn in row:
            keyboard_row.append(create_button(**btn))
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(keyboard)

def create_pagination_keyboard(current_page: int, total_pages: int, prefix: str) -> List[List[Dict]]:
    """Create pagination keyboard"""
    buttons = []
    
    # Navigation buttons
    nav_row = []
    if current_page > 1:
        nav_row.append({"text": "⬅️ Previous", "callback_data": f"{prefix}_page_{current_page-1}", "style": "secondary"})
    
    nav_row.append({"text": f"📄 {current_page}/{total_pages}", "callback_data": "noop", "style": "info"})
    
    if current_page < total_pages:
        nav_row.append({"text": "Next ➡️", "callback_data": f"{prefix}_page_{current_page+1}", "style": "secondary"})
    
    buttons.append(nav_row)
    return buttons

def build_user_list_menu(users: List[Dict], current_page: int, total_users: int, limit: int) -> InlineKeyboardMarkup:
    """Builds an inline keyboard for listing users with pagination."""
    keyboard_buttons = []
    for user in users:
        status_emoji = "🟢" if not user.get("banned", False) else "🔴"
        username = user.get("username", "N/A")
        role_name = user.get("role_name", "N/A")
        keyboard_buttons.append([
            {"text": f"{status_emoji} {username} ({role_name})", "callback_data": f"admin_user_select_{user['id']}", "style": "info"}
        ])

    # Pagination controls
    total_pages = (total_users + limit - 1) // limit
    pagination_row = []
    if current_page > 1:
        pagination_row.append({"text": "⬅️", "callback_data": f"admin_user_page_{current_page-1}", "style": "secondary"})
    pagination_row.append({"text": f"{current_page}/{total_pages}", "callback_data": "noop", "style": "info"})
    if current_page < total_pages:
        pagination_row.append({"text": "➡️", "callback_data": f"admin_user_page_{current_page+1}", "style": "secondary"})
    
    if pagination_row:
        keyboard_buttons.append(pagination_row)

    # Other actions
    keyboard_buttons.append([
        {"text": "🔍 Search User", "callback_data": "admin_user_search", "style": "primary"},
        {"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"}
    ])
    return create_keyboard(keyboard_buttons)

def build_user_management_menu(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    """Builds an inline keyboard for managing a specific user."""
    ban_text = "✅ Unban User" if is_banned else "🚫 Ban User"
    ban_callback = f"admin_user_unban_{user_id}" if is_banned else f"admin_user_ban_{user_id}"
    
    keyboard_buttons = [
        [
            {"text": "💎 Edit ZC Balance", "callback_data": f"admin_user_editzc_{user_id}", "style": "premium"},
            {"text": "👑 Set Role", "callback_data": f"admin_user_setrole_{user_id}", "style": "info"},
        ],
        [
            {"text": ban_text, "callback_data": ban_callback, "style": "danger" if not is_banned else "success"},
        ],
        [
            {"text": "🔙 Back to User List", "callback_data": "admin_users", "style": "secondary"},
        ]
    ]
    return create_keyboard(keyboard_buttons)

def build_role_selection_keyboard(user_id: int, roles: List[Dict]) -> InlineKeyboardMarkup:
    """Builds an inline keyboard for selecting a role for a user."""
    keyboard_buttons = []
    for role in roles:
        keyboard_buttons.append([
            {"text": role["name"], "callback_data": f"admin_role_select_{role['role_id']}", "style": "info"}
        ])
    keyboard_buttons.append([
        {"text": "❌ Cancel", "callback_data": f"admin_user_select_{user_id}", "style": "secondary"}
    ])
    return create_keyboard(keyboard_buttons)

def build_cancel_keyboard(callback_data_on_cancel: str) -> InlineKeyboardMarkup:
    """Builds a simple keyboard with a cancel button."""
    return create_keyboard([
        [{"text": "❌ Cancel", "callback_data": callback_data_on_cancel, "style": "secondary"}]
    ])

def build_broadcast_menu() -> InlineKeyboardMarkup:
    """Builds the main broadcast menu."""
    keyboard_buttons = [
        [{"text": "➕ New Broadcast", "callback_data": "broadcast_new", "style": "primary"}],
        [{"text": "🔙 Back", "callback_data": "admin_panel", "style": "secondary"}]
    ]
    return create_keyboard(keyboard_buttons)

def build_broadcast_target_menu(roles: List[Dict]) -> InlineKeyboardMarkup:
    """Builds a menu for selecting broadcast target roles with an 'Everyone' option."""
    keyboard_buttons = []
    
    # Add "Everyone" option
    keyboard_buttons.append([
        {"text": "👥 Everyone (All Users)", "callback_data": "broadcast_target_0", "style": "primary"} # role_id 0 for everyone
    ])

    # Add roles in rows of two
    current_row = []
    for role in roles:
        current_row.append({"text": role["name"], "callback_data": f"broadcast_target_{role['role_id']}", "style": "info"})
        if len(current_row) == 2:
            keyboard_buttons.append(current_row)
            current_row = []
    if current_row: # Add any remaining button
        keyboard_buttons.append(current_row)

    keyboard_buttons.append([
        {"text": "❌ Cancel Broadcast", "callback_data": "broadcast_cancel", "style": "secondary"}
    ])
    return create_keyboard(keyboard_buttons)

def build_broadcast_confirmation_menu() -> InlineKeyboardMarkup:
    """Builds a confirmation menu for broadcasting."""
    keyboard_buttons = [
        [
            {"text": "✅ Confirm Broadcast", "callback_data": "broadcast_confirm_yes", "style": "danger"},
            {"text": "❌ Cancel", "callback_data": "broadcast_confirm_no", "style": "secondary"},
        ]
    ]
    return create_keyboard(keyboard_buttons)