import asyncio
import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from ...database.db_management import DatabaseManager
from ...utils.keyboards import create_keyboard
from ...config import ADMIN_IDS, logger

async def handle_admin_analytics(query):
    """Handle analytics"""
    analytics_menu = [
        [
            {"text": "🛠️ Tool Stats", "callback_data": "admin_tool_stats", "style": "info"},
            {"text": "⚠️ Error Reports", "callback_data": "admin_errors", "style": "warning"},
        ],
        [
            {"text": "📈 Growth Stats", "callback_data": "admin_growth", "style": "info"},
            {"text": "📊 Detailed Report", "callback_data": "admin_detailed_report", "style": "info"},
        ],
        [
            {"text": "🔄 Refresh Data", "callback_data": "admin_refresh_analytics", "style": "info"},
            {"text": "📤 Export Analytics", "callback_data": "admin_export_analytics", "style": "info"},
        ],
        [
            {"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"},
        ]
    ]

    await query.edit_message_text(
        text="📊 ANALYTICS DASHBOARD\n\n"
             "View system analytics and reports:\n\n"
             "• 🛠️ Tool Stats: Tool usage statistics\n"
             "• ⚠️ Error Reports: System error reports\n"
             "• 📈 Growth Stats: User growth analytics\n"
             "• 📊 Detailed Report: Comprehensive report\n"
             "• 🔄 Refresh Data: Update analytics data\n"
             "• 📤 Export Analytics: Export analytics data",
        reply_markup=create_keyboard(analytics_menu)
    )

async def handle_admin_tool_stats(query) -> None:
    db = await DatabaseManager.load_db()
    analytics = db.get("analytics", {})
    popular_tools = analytics.get("popular_tools", {})
    
    if not popular_tools:
        stats_text = "🛠️ No tool usage data available yet."
    else:
        stats_text = "🛠️ Tool Usage Statistics:\n\n"
        sorted_tools = sorted(popular_tools.items(), key=lambda x: x[1], reverse=True)
        for tool, count in sorted_tools[:15]:  # Top 15 tools
            tool_name = tool.replace('_', ' ').title()
            stats_text += f"• {tool_name}: {count} uses\n"
    
    await query.edit_message_text(
        text=stats_text,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Analytics", "callback_data": "admin_analytics", "style": "secondary"}]
        ])
    )

async def handle_admin_errors(query) -> None:
    db = await DatabaseManager.load_db()
    analytics = db.get("analytics", {})
    error_logs = analytics.get("error_logs", [])
    
    if not error_logs:
        error_text = "⚠️ No recent errors found. System running smoothly!"
    else:
        recent_errors = error_logs[-10:]  # Last 10 errors
        error_text = "⚠️ Recent Error Reports:\n\n"
        for i, error in enumerate(recent_errors, 1):
            error_type = error.get("error_type", "Unknown")
            timestamp = error.get("timestamp", "Unknown")[:19]
            error_text += f"{i}. {error_type} ({timestamp})\n"
    
    await query.edit_message_text(
        text=error_text,
        reply_markup=create_keyboard([
            [{"text": "🗑️ Clear Errors", "callback_data": "admin_clear_errors", "style": "danger"}],
            [{"text": "🔙 Back to Analytics", "callback_data": "admin_analytics", "style": "secondary"}]
        ])
    )

async def handle_admin_growth(query) -> None:
    db = await DatabaseManager.load_db()
    users = list(db["users"].values())
    
    # Calculate growth by day
    daily_signups = {}
    for user in users:
        try:
            join_date = user.get("joined_at", "")[:10]
            if join_date:
                daily_signups[join_date] = daily_signups.get(join_date, 0) + 1
        except:
            continue
    
    growth_text = "📈 User Growth (Last 7 Days):\n\n"
    
    if daily_signups:
        recent_days = sorted(daily_signups.keys())[-7:]  # Last 7 days
        for date in recent_days:
            count = daily_signups[date]
            growth_text += f"• {date}: {count} new users\n"
    else:
        growth_text += "No growth data available yet."
    
    await query.edit_message_text(
        text=growth_text,
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Analytics", "callback_data": "admin_analytics", "style": "secondary"}]
        ])
    )

async def generate_detailed_report(query):
    """Generate detailed system report"""
    db = await DatabaseManager.load_db()
    users = list(db["users"].values())
    stats = db.get("stats", {})
    analytics = db.get("analytics", {})
    
    # Calculate various metrics
    total_users = len(users)
    active_users = sum(1 for u in users if not u.get('banned', False))
    total_requests = stats.get('total_requests', 0)
    success_rate = (stats.get('successful_requests', 0) / max(total_requests, 1)) * 100
    
    report = (
        "📊 DETAILED SYSTEM REPORT\n\n"
        f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "👥 USER METRICS:\n"
        f"• Total Users: {total_users}\n"
        f"• Active Users: {active_users}\n"
        f"• Banned Users: {total_users - active_users}\n\n"
        "📈 REQUEST METRICS:\n"
        f"• Total Requests: {total_requests}\n"
        f"• Successful: {stats.get('successful_requests', 0)}\n"
        f"• Failed: {stats.get('failed_requests', 0)}\n"
        f"• Success Rate: {success_rate:.1f}%\n\n"
        "💎 CREDIT METRICS:\n"
        f"• Total Credits: {sum(u.get('credits', 0) for u in users)}\n"
        f"• Distributed: {stats.get('total_credits_distributed', 0)}\n\n"
        "🛠️ POPULAR TOOLS:\n"
    )
    
    popular_tools = analytics.get("popular_tools", {})
    if popular_tools:
        top_tools = sorted(popular_tools.items(), key=lambda x: x[1], reverse=True)[:5]
        for tool, count in top_tools:
            report += f"• {tool.replace('_', ' ').title()}: {count}\n"
    else:
        report += "• No usage data available\n"
    
    await query.edit_message_text(
        text=report,
        reply_markup=create_keyboard([
            [{"text": "💾 Export Report", "callback_data": "admin_export_report", "style": "info"}],
            [{"text": "🔙 Back to Analytics", "callback_data": "admin_analytics", "style": "secondary"}]
        ])
    )

async def clear_error_logs(query):
    """Clear error logs"""
    db = await DatabaseManager.load_db()
    
    if "analytics" not in db:
        db["analytics"] = {}
    db["analytics"]["error_logs"] = []
    
    await DatabaseManager.save_db(db)
    
    await query.edit_message_text(
        text="🗑️ Error logs cleared successfully!",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Analytics", "callback_data": "admin_analytics", "style": "secondary"}]
        ])
    )

async def export_data(query, context):
    """Export database data"""
    try:
        db = await DatabaseManager.load_db()
        
        # Create export data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bot_export_{timestamp}.json"
        
        # Create sanitized export (remove sensitive data)
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "version": "2.2",
                "total_users": len(db["users"])
            },
            "stats": db.get("stats", {}),
            "analytics": db.get("analytics", {}),
            "settings": {k: v for k, v in db.get("settings", {}).items() if k != "api_keys"},
            "api_config": {k: v for k, v in db.get("api_config", {}).items() if k != "API_KEY"}
        }
        
        with open(filename, "w") as f:
            json.dump(export_data, f, indent=4)
        
        # Send the file
        with open(filename, "rb") as f:
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=f,
                filename=filename,
                caption="📊 Bot Data Export (Anonymized)"
            )
        
        os.remove(filename)
        
        await query.edit_message_text(
            text="✅ Data exported successfully!",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"}]
            ])
        )
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        await query.edit_message_text(
            text=f"❌ Export failed: {str(e)}",
            reply_markup=create_keyboard([
                [{"text": "🔙 Back to Admin", "callback_data": "admin_panel", "style": "secondary"}]
            ])
        )
