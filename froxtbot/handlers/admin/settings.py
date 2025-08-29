from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...config import ADMIN_IDS, FORCE_JOIN_CHANNELS, BOT_NAME, SERVICES_CONFIG

async def handle_admin_settings(query):
    """Handle system settings"""
    settings_menu = [
        [
            {"text": "🤖 Bot Settings", "callback_data": "admin_bot_settings", "style": "info"},
            {"text": "💰 Credit Settings", "callback_data": "admin_credit_settings", "style": "premium"},
        ],
        [
            {"text": "🔌 API Settings", "callback_data": "admin_api_settings", "style": "info"},
            {"text": "📢 Channel Settings", "callback_data": "admin_channel_settings", "style": "info"},
        ],
        [
            {"text": "⚡ Rate Limits", "callback_data": "admin_rate_limits", "style": "warning"},
            {"text": "👑 Admin Management", "callback_data": "admin_admin_management", "style": "danger"},
        ],
        [
            {"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"},
        ]
    ]

    await query.edit_message_text(
        text="⚙️ SYSTEM SETTINGS\n\n"
             "Configure system parameters:\n\n"
             "• 🤖 Bot Settings: Bot configuration\n"
             "• 💰 Credit Settings: Credit system config\n"
             "• 🔌 API Settings: API endpoint management\n"
             "• 📢 Channel Settings: Force join channels\n"
             "• ⚡ Rate Limits: Request rate limiting\n"
             "• 👑 Admin Management: Manage admins",
        reply_markup=create_keyboard(settings_menu)
    )

async def handle_admin_bot_settings(query) -> None:
    db = await DatabaseManager.load_db()
    settings = db.get("settings", {})
    
    settings_text = (
        "🤖 Bot Settings\n\n"
        f"• Bot Name: {BOT_NAME}\n"
        f"• Version: 2.2\n"
        f"• Admin Count: {len(ADMIN_IDS)}\n"
        f"• Force Join: {len(FORCE_JOIN_CHANNELS)} channels\n"
        f"• Welcome Bonus: {settings.get('welcome_bonus', 2.0)} credits\n"
        f"• Referral Bonus: {settings.get('referral_bonus', 0.5)} credits\n"
        f"• Max Daily Requests: {settings.get('max_requests_per_day', 100)}\n"
        f"• Maintenance Mode: {'ON' if settings.get('maintenance_mode', False) else 'OFF'}\n"
    )
    
    await query.edit_message_text(
        text=settings_text,
        reply_markup=create_keyboard([
            [{"text": "🔄 Toggle Maintenance", "callback_data": "admin_toggle_maintenance", "style": "warning"}],
            [{"text": "🔙 Back to Settings", "callback_data": "admin_settings", "style": "secondary"}]
        ])
    )

async def handle_admin_credit_settings(query) -> None:
    # Get credit costs from SERVICES_CONFIG
    credit_costs = {tool: service_info["servicecost"] for tool, service_info in SERVICES_CONFIG.items()}
    
    settings_text = (
        "💰 Credit Settings\n\n"
        "⚙️ Current Credit Costs:\n"
    )
    
    for tool, cost in credit_costs.items():
        tool_name = tool.replace('_', ' ').title()
        cost_display = f"{cost} credits" if cost > 0 else "FREE"
        settings_text += f"• {tool_name}: {cost_display}\n"
    
    settings_text += "\n💡 Modify credit costs via API Configuration"
    
    await query.edit_message_text(
        text=settings_text,
        reply_markup=create_keyboard([
            [{"text": "🔧 API Configuration", "callback_data": "admin_api_config", "style": "info"}],
            [{"text": "🔙 Back to Settings", "callback_data": "admin_settings", "style": "secondary"}]
        ])
    )

async def toggle_maintenance_mode(query):
    """Toggle maintenance mode"""
    db = await DatabaseManager.load_db()
    current_mode = db.get("settings", {}).get("maintenance_mode", False)
    new_mode = not current_mode
    
    if "settings" not in db:
        db["settings"] = {}
    db["settings"]["maintenance_mode"] = new_mode
    await DatabaseManager.save_db(db)
    
    status = "ENABLED" if new_mode else "DISABLED"
    await query.edit_message_text(
        text=f"🔧 Maintenance Mode {status}\n\n"
             f"Status updated successfully!",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Settings", "callback_data": "admin_bot_settings", "style": "secondary"}]
        ])
    )

async def enable_maintenance_mode(query):
    """Enable maintenance mode"""
    db = await DatabaseManager.load_db()
    if "settings" not in db:
        db["settings"] = {}
    db["settings"]["maintenance_mode"] = True
    await DatabaseManager.save_db(db)
    
    await query.edit_message_text(
        text="🔧 Maintenance Mode ENABLED\n\n"
             "Bot is now in maintenance mode.\n"
             "Only admins can access the bot.",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"}]
        ])
    )

async def disable_maintenance_mode(query):
    """Disable maintenance mode"""
    db = await DatabaseManager.load_db()
    if "settings" not in db:
        db["settings"] = {}
    db["settings"]["maintenance_mode"] = False
    await DatabaseManager.save_db(db)
    
    await query.edit_message_text(
        text="✅ Maintenance Mode DISABLED\n\n"
             "Bot is now fully operational.\n"
             "All users can access the bot.",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"}]
        ])
    )

async def handle_admin_maintenance(query):
    """Handle maintenance mode settings"""
    db = await DatabaseManager.load_db()
    maintenance_mode = db.get("settings", {}).get("maintenance_mode", False)
    
    status = "ENABLED" if maintenance_mode else "DISABLED"
    
    maintenance_menu = [
        [
            {"text": f"{'✅ Disable' if maintenance_mode else '🔧 Enable'} Maintenance", 
             "callback_data": "admin_toggle_maintenance", 
             "style": "warning"},
        ],
        [
            {"text": "🔙 Back to Settings", "callback_data": "admin_settings", "style": "secondary"},
        ]
    ]
    
    maintenance_text = (
        f"🔧 Maintenance Mode: {status}\n\n"
        "Maintenance mode restricts bot access to admins only.\n"
        "Use this feature when performing system updates or repairs."
    )
    
    await query.edit_message_text(
        text=maintenance_text,
        reply_markup=create_keyboard(maintenance_menu)
    )
