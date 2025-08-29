from utils.keyboards import create_keyboard

async def show_upi_services(query):
    """Show UPI-related services"""
    upi_menu = [
        [
            {"text": "📱 Num to UPI", "callback_data": "tool_num2upi", "style": "primary"},
            {"text": "✅ UPI Verify", "callback_data": "tool_upi_verify", "style": "success"},
        ],
        [
            {"text": "💰 UPI Info", "callback_data": "tool_upi_info", "style": "info"},
        ],
        [
            {"text": "🔙 Back to Tools", "callback_data": "osint_tools", "style": "secondary"},
        ]
    ]

    await query.edit_message_text(
        text="💰 UPI Services\n\nSelect a service:",
        reply_markup=create_keyboard(upi_menu)
    )
