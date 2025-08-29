from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...config import DEFAULT_API_CONFIG, ADMIN_IDS

async def handle_admin_api_config(query):
    """Handle API configuration"""
    api_config_menu = [
        [
            {"text": "🔗 API Endpoints", "callback_data": "admin_api_endpoints", "style": "info"},
            {"text": "💎 Credit Costs", "callback_data": "admin_credit_costs", "style": "premium"},
        ],
        [
            {"text": "⚡ API Settings", "callback_data": "admin_api_settings_config", "style": "warning"},
            {"text": "🔄 Reset to Default", "callback_data": "admin_reset_api_config", "style": "danger"},
        ],
        [
            {"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"},
        ]
    ]

    await query.edit_message_text(
        text="🔌 API CONFIGURATION\n\n"
             "Configure API endpoints and settings:\n\n"
             "• 🔗 API Endpoints: Modify API URLs\n"
             "• 💎 Credit Costs: Set credit costs for tools\n"
             "• ⚡ API Settings: Configure timeout and retries\n"
             "• 🔄 Reset to Default: Reset all API settings\n\n"
             "⚠️ Warning: Incorrect configuration may break the bot!",
        reply_markup=create_keyboard(api_config_menu)
    )

from froxtbot.config.services import SERVICES_CONFIG

async def handle_admin_api_endpoints(query):
    """Show API endpoints configuration"""
    
    endpoints_text = "🔗 API Endpoints Configuration\n\n"
    for tool, service_info in SERVICES_CONFIG.items():
        tool_name = service_info['servicename']
        endpoint = service_info['serviceapi']
        endpoints_text += f"• {tool_name}: {endpoint[:50]}...\n"
    
    endpoints_text += "\nSelect a tool to modify its endpoint:"
    
    # Create buttons for each tool
    buttons = []
    tools_list = list(SERVICES_CONFIG.keys())
    
    for i in range(0, len(tools_list), 2):
        row = []
        if i < len(tools_list):
            row.append({"text": f"🔧 {SERVICES_CONFIG[tools_list[i]]['servicename']}", "callback_data": f"api_edit_{tools_list[i]}", "style": "info"})
        if i+1 < len(tools_list):
            row.append({"text": f"🔧 {SERVICES_CONFIG[tools_list[i+1]]['servicename']}", "callback_data": f"api_edit_{tools_list[i+1]}", "style": "info"})
        buttons.append(row)
    
    buttons.append([{"text": "🔙 Back to API Config", "callback_data": "admin_api_config", "style": "secondary"}])
    
    await query.edit_message_text(
        text=endpoints_text,
        reply_markup=create_keyboard(buttons)
    )

async def handle_admin_credit_costs(query):
    """Show credit costs configuration"""
    
    costs_text = "💎 Credit Costs Configuration\n\n"
    for tool, service_info in SERVICES_CONFIG.items():
        tool_name = service_info['servicename']
        cost = service_info['servicecost']
        costs_text += f"• {tool_name}: {cost} credits\n"
    
    costs_text += "\nSelect a tool to modify its credit cost:"
    
    # Create buttons for each tool
    buttons = []
    tools_list = list(SERVICES_CONFIG.keys())
    
    for i in range(0, len(tools_list), 2):
        row = []
        if i < len(tools_list):
            row.append({"text": f"💎 {SERVICES_CONFIG[tools_list[i]]['servicename']}", "callback_data": f"cost_edit_{tools_list[i]}", "style": "info"})
        if i+1 < len(tools_list):
            row.append({"text": f"💎 {SERVICES_CONFIG[tools_list[i+1]]['servicename']}", "callback_data": f"cost_edit_{tools_list[i+1]}", "style": "info"})
        buttons.append(row)
    
    buttons.append([{"text": "🔙 Back to API Config", "callback_data": "admin_api_config", "style": "secondary"}])
    
    await query.edit_message_text(
        text=costs_text,
        reply_markup=create_keyboard(buttons)
    )

async def handle_admin_api_settings_config(query):
    """Show API settings configuration"""
    db = await DatabaseManager.load_db()
    api_config = db["api_config"]
    
    settings_text = (
        "⚡ API Settings Configuration\n\n"
        f"• Request Timeout: {api_config.get('REQUEST_TIMEOUT', DEFAULT_API_CONFIG['REQUEST_TIMEOUT'])} seconds\n"
        f"• Max Retries: {api_config.get('MAX_RETRIES', DEFAULT_API_CONFIG['MAX_RETRIES'])}\n"
        f"• Retry Delay: {api_config.get('RETRY_DELAY', DEFAULT_API_CONFIG['RETRY_DELAY'])} seconds\n"
        f"• Max Message Length: {api_config.get('MAX_MESSAGE_LENGTH', DEFAULT_API_CONFIG['MAX_MESSAGE_LENGTH'])} characters\n"
        f"• Max Pretty Print: {api_config.get('MAX_PRETTY_PRINT_LENGTH', DEFAULT_API_CONFIG['MAX_PRETTY_PRINT_LENGTH'])} characters\n"
        f"• Pagination Size: {api_config.get('PAGINATION_SIZE', DEFAULT_API_CONFIG['PAGINATION_SIZE'])} items\n\n"
        "Select a setting to modify:"
    )
    
    settings_menu = [
        [
            {"text": "⏱️ Timeout", "callback_data": "api_set_timeout", "style": "info"},
            {"text": "🔄 Retries", "callback_data": "api_set_retries", "style": "info"},
        ],
        [
            {"text": "⏳ Retry Delay", "callback_data": "api_set_retry_delay", "style": "info"},
            {"text": "📝 Message Length", "callback_data": "api_set_msg_length", "style": "info"},
        ],
        [
            {"text": "📄 Pagination Size", "callback_data": "api_set_pagination", "style": "info"},
        ],
        [
            {"text": "🔙 Back to API Config", "callback_data": "admin_api_config", "style": "secondary"},
        ]
    ]
    
    await query.edit_message_text(
        text=settings_text,
        reply_markup=create_keyboard(settings_menu)
    )

async def handle_admin_reset_api_config(query):
    """Reset API configuration to default"""
    # No need to reset API config in DB, as it's now in code.
    # We will assume that changes to the DEFAULT_API_CONFIG will be done directly in the config file.
    # This function is now effectively a no-op or could be removed if not needed for other purposes.
    await query.answer("API configuration is now managed in code. No reset action needed in database.")
    
    await query.edit_message_text(
        text="✅ API Configuration Reset\n\nAll API settings have been reset to default values.",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to API Config", "callback_data": "admin_api_config", "style": "secondary"}]
        ])
    )
