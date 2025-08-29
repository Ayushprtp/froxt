from utils.keyboards import create_keyboard

async def show_news_updates(query):
    """Show news and updates"""
    await query.edit_message_text(
        text="📢 News & Updates\n\n"
             "• Version 2.2 released with new features!\n"
             "• Added Deep Scan tool with advanced mobile analysis\n"
             "• Implemented pagination for large results\n"
             "• Enhanced file export functionality\n"
             "• All APIs are fully configurable via admin panel\n"
             "• Improved response formatting and error handling\n\n"
             "Check back soon for more updates!",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"}]
        ])
    )
