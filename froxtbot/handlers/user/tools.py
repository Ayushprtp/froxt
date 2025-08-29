from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_users import UserManager
from ...database.db_management import DatabaseManager
from ...config.services import SERVICES_CONFIG
from ...utils.keyboards import create_keyboard

async def show_osint_tools(query, context):
    """Show the OSINT tools menu"""
    tools_menu = []
    
    # First row - Mobile and Email
    row1 = []
    if SERVICES_CONFIG.get("mobile", {}).get("enabled", True):
        row1.append({"text": "📱 Mobile Lookup", "callback_data": "tool_mobile", "style": "primary"})
    if SERVICES_CONFIG.get("email", {}).get("enabled", True):
        row1.append({"text": "📧 Email Lookup", "callback_data": "tool_email", "style": "primary"})
    if row1:
        tools_menu.append(row1)
    
    # Second row - Aadhar and UPI Services
    row2 = []
    if SERVICES_CONFIG.get("aadhar", {}).get("enabled", True):
        row2.append({"text": "🆔 Aadhar Search", "callback_data": "tool_aadhar", "style": "warning"})
    row2.append({"text": "💰 UPI Services", "callback_data": "upi_services", "style": "success"})
    if row2:
        tools_menu.append(row2)
    
    # Third row - Username and Password
    row3 = []
    if SERVICES_CONFIG.get("username_scan", {}).get("enabled", True):
        row3.append({"text": "🌐 Username Scan", "callback_data": "tool_username_scan", "style": "info"})
    if SERVICES_CONFIG.get("password_analyze", {}).get("enabled", True):
        row3.append({"text": "🔑 Password Analyze", "callback_data": "tool_password_analyze", "style": "warning"})
    if row3:
        tools_menu.append(row3)
    
    # Fourth row - Vehicle and Bike
    row4 = []
    if SERVICES_CONFIG.get("car_lookup", {}).get("enabled", True):
        row4.append({"text": "🚗 Vehicle Lookup", "callback_data": "tool_car_lookup", "style": "info"})
    if SERVICES_CONFIG.get("bike_info", {}).get("enabled", True):
        row4.append({"text": "🏍️ Bike Info", "callback_data": "tool_bike_info", "style": "info"})
    if row4:
        tools_menu.append(row4)
    
    # Fifth row - IP Scanner and Full Scan
    row5 = []
    if SERVICES_CONFIG.get("ip_scan", {}).get("enabled", True):
        row5.append({"text": "🌐 IP Scanner", "callback_data": "tool_ip_scan", "style": "secondary"})
    if SERVICES_CONFIG.get("full_scan", {}).get("enabled", True):
        row5.append({"text": "🔍 Full Scan", "callback_data": "tool_full_scan", "style": "secondary"})
    if row5:
        tools_menu.append(row5)
    
    # Sixth row - Deep Scan and Voter ID
    row6 = []
    if SERVICES_CONFIG.get("deep_scan", {}).get("enabled", True):
        row6.append({"text": "🔬 Deep Scan", "callback_data": "tool_deep_scan", "style": "premium"})
    if SERVICES_CONFIG.get("voterid", {}).get("enabled", True):
        row6.append({"text": "🗳️ Voter ID", "callback_data": "tool_voterid", "style": "info"})
    if row6:
        tools_menu.append(row6)
    
    # Seventh row - FamPay and Ration Card
    row7 = []
    if SERVICES_CONFIG.get("fam_pay", {}).get("enabled", True):
        row7.append({"text": "💳 FamPay Info", "callback_data": "tool_fam_pay", "style": "info"})
    if SERVICES_CONFIG.get("ration_card", {}).get("enabled", True):
        row7.append({"text": "🍞 Ration Card", "callback_data": "tool_ration_card", "style": "info"})
    if row7:
        tools_menu.append(row7)
    
    # Eighth row - Vehicle Info and Breach Check
    row8 = []
    if SERVICES_CONFIG.get("vehicle_info", {}).get("enabled", True):
        row8.append({"text": "🚙 Vehicle Info", "callback_data": "tool_vehicle_info", "style": "info"})
    if SERVICES_CONFIG.get("breach_check", {}).get("enabled", True):
        row8.append({"text": "🔓 Breach Check", "callback_data": "tool_breach_check", "style": "warning"})
    if row8:
        tools_menu.append(row8)
    
    # Back button
    tools_menu.append([
        {"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"},
    ])

    await query.edit_message_text(
        text="🛠️ OSINT Tools Menu\n\nSelect a tool to use:\n\n" 
             "🆓 Free Tools: Mobile, Email, Aadhar, UPI, Username, Password, IP, Full Scan, Bike, Voter ID, FamPay, Ration, Vehicle Info, Breach Check\n" 
             "💎 Premium Tools: Deep Scan (5 credits)",
        reply_markup=create_keyboard(tools_menu)
    )

async def handle_tool_selection(query, context, tool_name):
    """Handle tool selection"""
    user_id = query.from_user.id
    
    # Check if user has enough credits
    has_credits = await UserManager.has_enough_credits(user_id, tool_name)
    if not has_credits:
        service_info = SERVICES_CONFIG.get(tool_name, {})
        cost = service_info.get("servicecost", 0)
        user = await UserManager.get_user(user_id)
        user_credits = user.get('credits', 0) if user else 0
        await query.edit_message_text(
            text=f"❌ Insufficient Credits\n\n" 
                 f"You need {cost} credits to use this tool.\n" 
                 f"Your balance: {user_credits}\n\n" 
                 "Please buy more credits or use free tools.",
            reply_markup=create_keyboard([
                [{"text": "💳 Buy Credits", "callback_data": "buy_credits", "style": "success"}],
                [{"text": "🔙 Back to Tools", "callback_data": "osint_tools", "style": "secondary"}]
            ])
        )
        return
    
    # Store selected tool in context
    context.user_data["selected_tool"] = tool_name
    
    # Show input prompt
    tool_display_name = tool_name.replace('_', ' ').title()
    service_info = SERVICES_CONFIG.get(tool_name, {})
    cost = service_info.get("servicecost", 0)
    cost_text = f"💎 Cost: {cost} credits\n" if cost > 0 else "🆓 Free to use\n"
    
    # Get input prompt from service info
    prompt = service_info.get("input_prompt", "Enter search input")
    
    await query.edit_message_text(
        text=f"🔧 {tool_display_name}\n\n" 
             f"{cost_text}\n" 
             f"{prompt}:",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Tools", "callback_data": "osint_tools", "style": "secondary"}]
        ])
    )

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tools command"""
    # This function will be called from the main bot file, so it needs to import check_force_join
    from ...utils.join_checker import check_force_join
    if not await check_force_join(update, context):
        return
    
    class MockQuery:
        def __init__(self, user, message):
            self.from_user = user
            self.message = message
            
        async def edit_message_text(self, text, reply_markup=None):
            await self.message.reply_text(text, reply_markup=reply_markup)
    
    mock_query = MockQuery(update.effective_user, update.message)
    await show_osint_tools(mock_query, context)