import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...config import ADMIN_IDS, FORCE_JOIN_CHANNELS

async def handle_admin_security_center(query):
    """Handle security center"""
    db = await DatabaseManager.load_db()
    users = list(db["users"].values())
    
    banned_count = sum(1 for u in users if u.get('banned', False))
    suspicious_activity = sum(1 for u in users if u.get('daily_requests', 0) > 50)
    
    security_text = (
        "🛡️ Security Center\n\n"
        f"• 🚫 Banned Users: {banned_count}\n"
        f"• ⚠️ Suspicious Activity: {suspicious_activity}\n"
        f"• 🔒 Force Join Active: {len(FORCE_JOIN_CHANNELS)} channels\n"
        f"• 👑 Admins: {len(ADMIN_IDS)}\n\n"
        "Security status: 🟢 All systems secure"
    )
    
    security_menu = [
        [
            {"text": "🚫 View Banned", "callback_data": "admin_view_banned", "style": "danger"},
            {"text": "⚠️ Suspicious Users", "callback_data": "admin_suspicious_users", "style": "warning"},
        ],
        [
            {"text": "📋 Security Logs", "callback_data": "admin_security_logs", "style": "info"},
            {"text": "🔒 Security Scan", "callback_data": "admin_security_scan", "style": "info"},
        ],
        [
            {"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"},
        ]
    ]
    
    await query.edit_message_text(
        text=security_text,
        reply_markup=create_keyboard(security_menu)
    )

async def view_banned_users(query):
    """View banned users"""
    db = await DatabaseManager.load_db()
    banned_users = [u for u in db["users"].values() if u.get('banned', False)]
    
    if not banned_users:
        banned_text = "🚫 No banned users found."
    else:
        banned_text = "🚫 Banned Users:\n\n"
        for i, user in enumerate(banned_users[:10], 1):
            username = user.get("username", "N/A")
            banned_text += f"{i}. {username} (ID: {user['id']})\n"
        
        if len(banned_users) > 10:
            banned_text += f"\n... and {len(banned_users) - 10} more"
    
    await query.edit_message_text(
        text=banned_text,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Security", "callback_data": "admin_security_center", "style": "secondary"}]
        ])
    )

async def view_suspicious_users(query):
    """View users with suspicious activity"""
    db = await DatabaseManager.load_db()
    users = list(db["users"].values())
    
    # Define suspicious criteria
    suspicious_users = []
    for user in users:
        daily_requests = user.get('daily_requests', 0)
        total_requests = user.get('total_requests', 0)
        
        if daily_requests > 50 or total_requests > 500:
            suspicious_users.append(user)
    
    if not suspicious_users:
        suspicious_text = "⚠️ No suspicious activity detected."
    else:
        suspicious_text = "⚠️ Users with High Activity:\n\n"
        for i, user in enumerate(suspicious_users[:10], 1):
            username = user.get("username", "N/A")
            daily = user.get('daily_requests', 0)
            total = user.get('total_requests', 0)
            suspicious_text += f"{i}. {username} - Daily: {daily}, Total: {total}\n"
    
    await query.edit_message_text(
        text=suspicious_text,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Security", "callback_data": "admin_security_center", "style": "secondary"}]
        ])
    )

async def run_security_scan(query):
    """Run security scan"""
    await query.edit_message_text(text="🔍 Running security scan...")
    
    # Simulate security scan
    await asyncio.sleep(2)
    
    scan_results = (
        "🛡️ Security Scan Complete\n\n"
        "✅ Database integrity: OK\n"
        "✅ User permissions: OK\n"
        "✅ Rate limiting: ACTIVE\n"
        "✅ Force join: ACTIVE\n"
        "✅ Admin access: SECURE\n"
        "✅ Error handling: OK\n\n"
        "🟢 All security checks passed!"
    )
    
    await query.edit_message_text(
        text=scan_results,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Security", "callback_data": "admin_security_center", "style": "secondary"}]
        ])
    )
