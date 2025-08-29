import hashlib
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ..database.db_management import DatabaseManager
from ..database.db_users import UserManager
from ..database.db_exclusions import ExclusionManager
from ..api.client import execute_tool_request
from ..utils.formatters import format_response_for_telegram
from ..utils.keyboards import create_keyboard, create_pagination_keyboard
from ..utils.pagination import PaginationManager
from ..utils.join_checker import check_force_join
from ..config import DEFAULT_API_CONFIG, ADMIN_IDS, logger
from .admin.actions import admin_input_handler

async def handle_pagination(query, context, callback_data):
    """Handle pagination navigation"""
    try:
        parts = callback_data.split('_')
        if len(parts) < 4:
            await query.answer("❌ Invalid pagination data")
            return
        
        tool_name = '_'.join(parts[1:-2])  # Handle tool names with underscores
        page = int(parts[-1])
        
        pagination_key = f"pagination_{tool_name}"
        pagination_data = context.user_data.get(pagination_key)
        
        if not pagination_data:
            await query.answer("❌ Pagination data not found")
            return
        
        full_data = pagination_data["full_data"]
        
        # Get pagination size from config
        db = await DatabaseManager.load_db()
        page_size = db["api_config"].get("PAGINATION_SIZE", DEFAULT_API_CONFIG["PAGINATION_SIZE"])
        
        # Paginate the data
        paginated = PaginationManager.paginate_data(full_data, page, page_size)
        
        # Format the paginated data
        formatted_message, _, _ = format_response_for_telegram(paginated["page_data"], tool_name)
        
        # Create success header
        success_header = (
            f"✅ Results Retrieved\n\n"
            f"🔧 Tool: {tool_name.replace('_', ' ').title()}\n"
            f"📄 Page {paginated['current_page']}/{paginated['total_pages']}\n"
            f"📊 Items: {len(paginated['page_data'])}/{paginated['total_items']}\n\n"
        )
        
        # Create pagination buttons
        pagination_buttons = create_pagination_keyboard(
            paginated["current_page"],
            paginated["total_pages"],
            f"result_{tool_name}"
        )
        
        # Add back to menu button
        pagination_buttons.append([
            {"text": "🔙 Back to Tools", "callback_data": "osint_tools", "style": "secondary"}
        ])
        
        # Update pagination data in context
        context.user_data[pagination_key]["current_page"] = page
        
        full_message = f"{success_header}{formatted_message}"
        await query.edit_message_text(
            text=full_message,
            parse_mode='Markdown',
            reply_markup=create_keyboard(pagination_buttons)
        )
        
        await query.answer(f"📄 Page {page}")
        
    except Exception as e:
        logger.error(f"Error in pagination: {e}")
        await query.answer("❌ Pagination error occurred")

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process user input for OSINT tools"""
    if not await check_force_join(update, context):
        return

    user_id = update.message.from_user.id
    
    # Check if in admin input mode
    if user_id in ADMIN_IDS and context.user_data.get("admin_action"):
        await admin_input_handler(update, context)
        return
    
    user_data = await UserManager.get_user(user_id)
    selected_tool = context.user_data.get("selected_tool")

    if not selected_tool:
        await update.message.reply_text(
            "❌ Please select a tool from the menu first!",
            reply_markup=create_keyboard([
                [{"text": "🛠️ Open Tools Menu", "callback_data": "osint_tools", "style": "primary"}]
            ])
        )
        return

    if not user_data or user_data.get("banned", False):
        await update.message.reply_text("🚫 Access denied. You are banned from using this bot.")
        return

    # Check maintenance mode
    db = await DatabaseManager.load_db()
    if db.get("settings", {}).get("maintenance_mode", False) and user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "🔧 Bot is currently under maintenance.\n"
            "Please try again later."
        )
        return

    can_proceed, limit_message = await UserManager.check_rate_limit(user_id)
    if not can_proceed:
        await update.message.reply_text(f"⏰ Rate Limited\n\n{limit_message}")
        return

    input_text = update.message.text.strip()

    # Check for exclusion
    exclusion = await ExclusionManager.get_exclusion(input_text)
    if exclusion:
        logger.info(f"User {user_id} queried an excluded item: '{input_text}'. Returning exclusion message.")
        await update.message.reply_text(
            f"🚫 Exclusion Alert!\n\n"
            f"Your query for '{input_text}' is in the exclusion list.\n"
            f"Message: {exclusion['message']}\n\n"
            f"No credits were deducted for this query."
        )
        # Clear selected tool
        context.user_data.pop("selected_tool", None)
        return

    # Send immediate processing message
    processing_msg = await update.message.reply_text(
        "⚡ Processing your request...\n\n"
        f"🔧 Tool: {selected_tool.replace('_', ' ').title()}\n"
        f"📊 Analyzing data..."
    )

    try:
        # Execute the request
        result = await execute_tool_request(selected_tool, input_text)
        
        if result.get("error"):
            error_msg = (
                f"❌ Request Failed\n\n"
                f"🔧 Tool: {selected_tool.replace('_', ' ').title()}\n"
                f"⚠️ Error: {result['error']}\n"
            )
            if result.get("message"):
                error_msg += f"📋 Details: {result['message']}"
            
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=error_msg
            )
            
            # Update failed requests counter
            db = await DatabaseManager.load_db()
            db["stats"]["failed_requests"] = db["stats"].get("failed_requests", 0) + 1
            await DatabaseManager.save_db(db)
            return

        # Deduct credits and update stats
        # Credits are only deducted if the query is NOT in the exclusion list
        await UserManager.deduct_credits(user_id, selected_tool)
        db = await DatabaseManager.load_db()
        # Get credit costs from the SERVICES configuration
        services_config = db["api_config"].get("SERVICES", DEFAULT_API_CONFIG["SERVICES"])
        service_info = services_config.get(selected_tool, {})
        cost = service_info.get("servicecost", 0)

        # Format response for Telegram with pagination
        formatted_message, file_data, pagination_data = format_response_for_telegram(result, selected_tool)
        
        # Create success header
        credits_message = f"💎 Credits used: {cost}\n" if cost > 0 else "🆓 Free tool used\n"
        success_header = (
            f"✅ Results Retrieved\n\n"
            f"🔧 Tool: {selected_tool.replace('_', ' ').title()}\n"
            f"{credits_message}"
            f"📊 Data processed successfully\n\n"
        )

        # If we have pagination data, store it in context for navigation
        if pagination_data:
            context.user_data[f"pagination_{selected_tool}"] = {
                "full_data": result,
                "tool_name": selected_tool,
                "current_page": 1
            }

        # If we need to send a file
        if file_data:
            filename, file_content = file_data
            
            # Update processing message with results and pagination
            pagination_buttons = []
            if pagination_data and pagination_data.get("total_pages", 1) > 1:
                pagination_buttons = create_pagination_keyboard(
                    pagination_data["current_page"],
                    pagination_data["total_pages"],
                    f"result_{selected_tool}"
                )
            
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=f"{success_header}{formatted_message}",
                parse_mode='Markdown',
                reply_markup=create_keyboard(pagination_buttons) if pagination_buttons else None
            )
            
            # Create and send file
            with open(filename, "w", encoding='utf-8') as f:
                f.write(file_content)
            
            try:
                with open(filename, "rb") as f:
                    await update.message.reply_document(
                        document=f,
                        caption=f"📄 Complete results for {selected_tool.replace('_', ' ')} query\n"
                               f"📊 Total items: {pagination_data.get('total_items', 'N/A')}",
                        filename=filename
                    )
                os.remove(filename)
            except Exception as e:
                logger.error(f"Error sending file: {e}")
                await update.message.reply_text(f"⚠️ File creation error: {str(e)}")
        else:
            # Send normal message with pagination if needed
            pagination_buttons = []
            if pagination_data and pagination_data.get("total_pages", 1) > 1:
                pagination_buttons = create_pagination_keyboard(
                    pagination_data["current_page"],
                    pagination_data["total_pages"],
                    f"result_{selected_tool}"
                )
            
            full_message = f"{success_header}{formatted_message}"
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=full_message,
                parse_mode='Markdown',
                reply_markup=create_keyboard(pagination_buttons) if pagination_buttons else None
            )

        # Update successful requests counter
        db = await DatabaseManager.load_db()
        db["stats"]["successful_requests"] = db["stats"].get("successful_requests", 0) + 1
        await DatabaseManager.save_db(db)

    except Exception as e:
        logger.error(f"Error processing {selected_tool}: {e}")
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text=f"❌ Processing Error\n\n"
            f"⚠️ An unexpected error occurred. Our team has been notified.\n"
            f"🔄 Please try again in a few moments.\n\n"
            f"🆔 Error ID: {hashlib.md5(str(e).encode()).hexdigest()[:8]}",
            parse_mode='Markdown'
        )
        
        # Log error to database
        db = await DatabaseManager.load_db()
        if "analytics" not in db:
            db["analytics"] = {"error_logs": []}
        if "error_logs" not in db["analytics"]:
            db["analytics"]["error_logs"] = []
            
        db["analytics"]["error_logs"].append({
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "tool": selected_tool,
            "error": str(e),
            "input_hash": hashlib.md5(input_text.encode()).hexdigest()
        })
        db["analytics"]["error_logs"] = db["analytics"]["error_logs"][-100:]  # Keep last 100 errors
        await DatabaseManager.save_db(db)

    # Clear selected tool
    context.user_data.pop("selected_tool", None)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    logger.info(f"Button pressed: user={user_id}, data={data}")
    
    try:
        # Import handlers dynamically to avoid circular dependencies
        from .user.start import start
        from .user.dashboard import show_user_dashboard
        from .user.tools import show_osint_tools, handle_tool_selection
        from .user.upi_services import show_upi_services
        from .user.news_updates import show_news_updates
        from .user.usage_history import show_usage_history
        from .user.achievements import show_achievements
        from .user.referral import show_refer_earn
        from .user.shop import show_buy_credits, show_item_confirmation, handle_and_redirect_purchase_request
        from .user.support import contact_support
        from .user.exclusion_management import (
            show_user_exclusion_management_panel, view_user_exclusions, handle_user_view_exclusions_pagination,
            handle_select_fill_slot, delete_user_exclusion_confirmed, clear_user_exclusion_slot_confirmed
        )
        from .admin.actions import handle_admin_action
        
        if data == "check_membership":
            if await check_force_join(update, context):
                await start(update, context)
        
        elif data == "noop":
            # No operation - used for display-only buttons
            pass
                
        elif data.startswith("tool_"):
            tool_name = data.replace("tool_", "")
            await handle_tool_selection(query, context, tool_name)
        
        elif data.startswith("result_") and "_page_" in data:
            await handle_pagination(query, context, data)
            
        elif data == "osint_tools":
            await show_osint_tools(query, context)
            
        elif data == "my_dashboard":
            await show_user_dashboard(query)
            
        elif data == "refer_earn":
            await show_refer_earn(query, context)
            
        elif data == "buy_credits":
            await show_buy_credits(query)
            
        elif data == "contact_support":
            await contact_support(query)
            
        elif data == "news_updates":
            await show_news_updates(query)
            
        elif data == "usage_history":
            await show_usage_history(query)
            
        elif data == "achievements":
            await show_achievements(query)
            
        elif data == "admin_panel":
            if user_id in ADMIN_IDS:
                from .admin.dashboard import show_admin_panel
                await show_admin_panel(query)
            else:
                await query.edit_message_text("❌ Unauthorized access")
                
        elif data == "back_to_menu":
            await start(update, context)
            
        elif data == "upi_services":
            await show_upi_services(query)
            
        elif data.startswith("user_shop_select_"):
            await show_item_confirmation(update, context)

        elif data.startswith("user_shop_confirm_"):
            await handle_and_redirect_purchase_request(update, context)
        
        # User Exclusion Management
        elif data == "user_exclusion_management":
            await show_user_exclusion_management_panel(query, context)
        elif data == "user_view_exclusions":
            await view_user_exclusions(query, context)
        elif data.startswith("user_view_exclusions_page_"):
            await handle_user_view_exclusions_pagination(query, context, data)
        elif data.startswith("user_select_fill_slot_"):
            await handle_select_fill_slot(query, context)
        elif data.startswith("user_delete_exclusion_confirm_"):
            await delete_user_exclusion_confirmed(query, context)
        elif data.startswith("user_clear_exclusion_slot_confirm_"):
            await clear_user_exclusion_slot_confirmed(query, context)
        
        # User Usage History Pagination
        elif data.startswith("user_usage_history_page_"):
            from .user.usage_history import handle_usage_history_pagination
            await handle_usage_history_pagination(query, context, data)
            
        elif data.startswith("admin_"):
            if user_id in ADMIN_IDS:
                from .admin.dashboard import show_admin_panel
                await show_admin_panel(query)
            else:
                await query.edit_message_text("❌ Unauthorized access")
                
        else:
            await query.edit_message_text("❌ Unknown action selected")
            
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        await query.edit_message_text("❌ An error occurred while processing your request")