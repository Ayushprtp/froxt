import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...config import ADMIN_IDS, DEFAULT_API_CONFIG, logger
from ...config.services import SERVICES_CONFIG

# Import handlers for various admin sections
from .user_management import start_user_management
from .credit_management import handle_admin_credits, credit_management_conversation
from .broadcast_management import new_broadcast_start, broadcast_conversation_handler
from .analytics import (
    handle_admin_analytics, handle_admin_tool_stats, handle_admin_errors, handle_admin_growth,
    generate_detailed_report, clear_error_logs, export_data
)
from .settings import (
    handle_admin_settings, handle_admin_bot_settings, handle_admin_credit_settings,
    toggle_maintenance_mode, enable_maintenance_mode, disable_maintenance_mode, handle_admin_maintenance
)
from .api_config import (
    handle_admin_api_config, handle_admin_api_endpoints, handle_admin_credit_costs,
    handle_admin_api_settings_config, handle_admin_reset_api_config
)
from .security import (
    handle_admin_security_center, view_banned_users, view_suspicious_users, run_security_scan
)
from .exclusion_management import (
    show_exclusion_management_panel, view_exclusions, handle_view_exclusions_pagination,
    delete_exclusion_confirmed
)
from .history_management import (
    show_history_management_panel, view_all_queries, handle_all_queries_pagination, search_queries
)


async def handle_admin_action(query, context, action: str) -> None:
    """Enhanced admin action handler"""
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text(text="🚫 Unauthorized access denied.")
        return

    try:
        # Main admin sections
        if action == "users":
            await start_user_management(query, context) # Start user management conversation
        elif action == "credits":
            await handle_admin_credits(query) # Display credit management menu
        elif action == "analytics":
            await handle_admin_analytics(query)
        elif action == "settings":
            await handle_admin_settings(query)
        elif action == "broadcast":
            await new_broadcast_start(query, context) # Start broadcast conversation
        elif action == "export":
            await export_data(query, context)
        elif action == "security_center":
            await handle_admin_security_center(query)
        elif action == "maintenance":
            await handle_admin_maintenance(query)
        elif action == "api_config":
            await handle_admin_api_config(query)
        elif action == "exclusion_management":
            await show_exclusion_management_panel(query, context)
        elif action == "view_exclusions":
            await view_exclusions(query, context)
        elif action.startswith("admin_view_exclusions_page_"):
            await handle_view_exclusions_pagination(query, context, action)
        elif action.startswith("admin_delete_exclusion_confirm_"):
            await delete_exclusion_confirmed(query, context)
        elif action == "api_endpoints":
            await handle_admin_api_endpoints(query)
        elif action == "credit_costs":
            await handle_admin_credit_costs(query)
        elif action == "api_settings_config":
            await handle_admin_api_settings_config(query)
        elif action == "reset_api_config":
            await handle_admin_reset_api_config(query)
        elif action == "history_management":
            await show_history_management_panel(query, context)
        elif action == "view_all_queries":
            await view_all_queries(query, context)
        elif action.startswith("admin_view_all_queries_page_"):
            await handle_all_queries_pagination(query, context, action)
        elif action == "search_queries":
            await search_queries(query, context)
        
        # API endpoint editing (still handled directly as it's a simple input)
        elif action.startswith("api_edit_"):
            tool = action.replace("api_edit_", "")
            # Endpoints are now directly in SERVICES_CONFIG
            current_endpoint = SERVICES_CONFIG.get(tool, {}).get("serviceapi", "Not set")
            await query.edit_message_text(
                text=f"🔧 Edit API Endpoint for {tool}\n\nCurrent endpoint:\n`{current_endpoint}`\n\nSend the new endpoint URL:",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "❌ Cancel", "callback_data": "admin_api_endpoints", "style": "secondary"}]
                ])
            )
            context.user_data["admin_action"] = f"edit_api_{tool}"
        
        # Credit cost editing (still handled directly as it's a simple input)
        elif action.startswith("cost_edit_"):
            tool = action.replace("cost_edit_", "")
            # Credit costs are now directly in SERVICES_CONFIG
            current_cost = SERVICES_CONFIG.get(tool, {}).get("servicecost", 0)
            
            await query.edit_message_text(
                text=f"💎 Edit Credit Cost for {tool}\n\nCurrent cost: {current_cost} credits\n\nSend the new cost (number only):",
                reply_markup=create_keyboard([
                    [{"text": "❌ Cancel", "callback_data": "admin_credit_costs", "style": "secondary"}]
                ])
            )
            context.user_data["admin_action"] = f"edit_cost_{tool}"
        
        # API settings editing (still handled directly as it's a simple input)
        elif action == "api_set_timeout":
            current_timeout = DEFAULT_API_CONFIG["REQUEST_TIMEOUT"]
            await query.edit_message_text(
                text=f"⏱️ Set API Timeout\n\nCurrent timeout: {current_timeout} seconds\n\nSend the new timeout in seconds:",
                reply_markup=create_keyboard([
                    [{"text": "❌ Cancel", "callback_data": "admin_api_settings_config", "style": "secondary"}]
                ])
            )
            context.user_data["admin_action"] = "set_timeout"
        elif action == "api_set_retries":
            current_retries = DEFAULT_API_CONFIG["MAX_RETRIES"]
            await query.edit_message_text(
                text=f"🔄 Set Max Retries\n\nCurrent retries: {current_retries}\n\nSend the new max retries:",
                reply_markup=create_keyboard([
                    [{"text": "❌ Cancel", "callback_data": "admin_api_settings_config", "style": "secondary"}]
                ])
            )
            context.user_data["admin_action"] = "set_retries"
        elif action == "api_set_retry_delay":
            current_delay = DEFAULT_API_CONFIG["RETRY_DELAY"]
            await query.edit_message_text(
                text=f"⏳ Set Retry Delay\n\nCurrent delay: {current_delay} seconds\n\nSend the new retry delay in seconds:",
                reply_markup=create_keyboard([
                    [{"text": "❌ Cancel", "callback_data": "admin_api_settings_config", "style": "secondary"}]
                ])
            )
            context.user_data["admin_action"] = "set_retry_delay"
        elif action == "api_set_msg_length":
            current_length = DEFAULT_API_CONFIG["MAX_MESSAGE_LENGTH"]
            await query.edit_message_text(
                text=f"📝 Set Max Message Length\n\nCurrent length: {current_length} characters\n\nSend the new max message length:",
                reply_markup=create_keyboard([
                    [{"text": "❌ Cancel", "callback_data": "admin_api_settings_config", "style": "secondary"}]
                ])
            )
            context.user_data["admin_action"] = "set_msg_length"
        elif action == "api_set_pagination":
            current_size = DEFAULT_API_CONFIG["PAGINATION_SIZE"]
            await query.edit_message_text(
                text=f"📄 Set Pagination Size\n\nCurrent size: {current_size} items per page\n\nSend the new pagination size:",
                reply_markup=create_keyboard([
                    [{"text": "❌ Cancel", "callback_data": "admin_api_settings_config", "style": "secondary"}]
                ])
            )
            context.user_data["admin_action"] = "set_pagination"
        
        # Analytics sub-actions
        elif action == "tool_stats":
            await handle_admin_tool_stats(query)
        elif action == "errors":
            await handle_admin_errors(query)
        elif action == "growth":
            await handle_admin_growth(query)
        elif action == "detailed_report":
            await generate_detailed_report(query)
        elif action == "clear_errors":
            await clear_error_logs(query)
        
        # Settings sub-actions
        elif action == "bot_settings":
            await handle_admin_bot_settings(query)
        elif action == "credit_settings":
            await handle_admin_credit_settings(query)
        elif action == "toggle_maintenance":
            await toggle_maintenance_mode(query)
        elif action == "enable_maintenance":
            await enable_maintenance_mode(query)
        elif action == "disable_maintenance":
            await disable_maintenance_mode(query)
        
        # Security sub-actions
        elif action == "view_banned":
            await view_banned_users(query)
        elif action == "suspicious_users":
            await view_suspicious_users(query)
        elif action == "security_scan":
            await run_security_scan(query)
        
        else:
            await query.edit_message_text(
                text="❌ Invalid admin action.",
                reply_markup=create_keyboard([
                    [{"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"}]
                ])
            )
    except Exception as e:
        logger.error(f"Error in admin action {action}: {e}")
        await query.edit_message_text(
            text=f"❌ Error executing admin action: {str(e)}",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"}]
            ])
        )

async def admin_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin text inputs for various operations"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    text = update.message.text.strip()
    action = context.user_data.get("admin_action")
    
    if not action:
        return
    
    # Check if the action is part of a conversation handler
    # If so, the input will be handled by the conversation handler, not here.
    if action in ["add_exclusion_value", "add_exclusion_message", 
                  "edit_exclusion_select", "edit_exclusion_value", "edit_exclusion_message",
                  "delete_exclusion_select"]:
        # The conversation handler will manage context.user_data["admin_action"]
        return
    
    try:
        # API configuration actions
        if action.startswith("edit_api_"):
            tool = action.replace("edit_api_", "")
            # In-memory update for SERVICES_CONFIG (this will not persist across bot restarts
            # unless written back to froxtbot/config/services.py file)
            if tool in SERVICES_CONFIG:
                SERVICES_CONFIG[tool]["serviceapi"] = text
                await update.message.reply_text(f"✅ API endpoint for {tool} updated successfully! (Note: This change is in-memory and will be lost on bot restart unless saved to file.)")
            else:
                await update.message.reply_text(f"❌ Service '{tool}' not found in configuration.")
            
        elif action.startswith("edit_cost_"):
            tool = action.replace("edit_cost_", "")
            try:
                cost = float(text)
                if cost < 0:
                    await update.message.reply_text("❌ Cost cannot be negative.")
                    return

                # In-memory update for SERVICES_CONFIG (this will not persist across bot restarts
                # unless written back to froxtbot/config/services.py file)
                if tool in SERVICES_CONFIG:
                    SERVICES_CONFIG[tool]["servicecost"] = cost
                    await update.message.reply_text(f"✅ Credit cost for {tool} updated to {cost} credits! (Note: This change is in-memory and will be lost on bot restart unless saved to file.)")
                else:
                    await update.message.reply_text(f"❌ Service '{tool}' not found in configuration.")
            except ValueError:
                await update.message.reply_text("❌ Invalid cost. Enter a number.")
                
        elif action == "set_timeout":
            try:
                timeout = int(text)
                if timeout <= 0:
                    await update.message.reply_text("❌ Timeout must be positive.")
                    return

                # In-memory update for DEFAULT_API_CONFIG (this will not persist across bot restarts
                # unless written back to froxtbot/config.py file)
                DEFAULT_API_CONFIG["REQUEST_TIMEOUT"] = timeout
                await update.message.reply_text(f"✅ API timeout updated to {timeout} seconds! (Note: This change is in-memory and will be lost on bot restart unless saved to file.)")
            except ValueError:
                await update.message.reply_text("❌ Invalid timeout. Enter a number.")
                
        elif action == "set_retries":
            try:
                retries = int(text)
                if retries <= 0:
                    await update.message.reply_text("❌ Retries must be positive.")
                    return

                # In-memory update for DEFAULT_API_CONFIG (this will not persist across bot restarts
                # unless written back to froxtbot/config.py file)
                DEFAULT_API_CONFIG["MAX_RETRIES"] = retries
                await update.message.reply_text(f"✅ Max retries updated to {retries}! (Note: This change is in-memory and will be lost on bot restart unless saved to file.)")
            except ValueError:
                await update.message.reply_text("❌ Invalid retries. Enter a number.")
                
        elif action == "set_retry_delay":
            try:
                delay = float(text)
                if delay <= 0:
                    await update.message.reply_text("❌ Delay must be positive.")
                    return

                # In-memory update for DEFAULT_API_CONFIG (this will not persist across bot restarts
                # unless written back to froxtbot/config.py file)
                DEFAULT_API_CONFIG["RETRY_DELAY"] = delay
                await update.message.reply_text(f"✅ Retry delay updated to {delay} seconds! (Note: This change is in-memory and will be lost on bot restart unless saved to file.)")
            except ValueError:
                await update.message.reply_text("❌ Invalid delay. Enter a number.")
                
        elif action == "set_msg_length":
            try:
                length = int(text)
                if length <= 0:
                    await update.message.reply_text("❌ Length must be positive.")
                    return

                # In-memory update for DEFAULT_API_CONFIG (this will not persist across bot restarts
                # unless written back to froxtbot/config.py file)
                DEFAULT_API_CONFIG["MAX_MESSAGE_LENGTH"] = length
                await update.message.reply_text(f"✅ Max message length updated to {length} characters! (Note: This change is in-memory and will be lost on bot restart unless saved to file.)")
            except ValueError:
                await update.message.reply_text("❌ Invalid length. Enter a number.")
                
        elif action == "set_pagination":
            try:
                size = int(text)
                if size <= 0:
                    await update.message.reply_text("❌ Size must be positive.")
                    return

                # In-memory update for DEFAULT_API_CONFIG (this will not persist across bot restarts
                # unless written back to froxtbot/config.py file)
                DEFAULT_API_CONFIG["PAGINATION_SIZE"] = size
                await update.message.reply_text(f"✅ Pagination size updated to {size} items! (Note: This change is in-memory and will be lost on bot restart unless saved to file.)")
            except ValueError:
                await update.message.reply_text("❌ Invalid size. Enter a number.")
            
        else:
            await update.message.reply_text("❌ Unknown admin action.")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid input format.")
    except Exception as e:
        logger.error(f"Error in admin input handler: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

    context.user_data.pop("admin_action", None)
