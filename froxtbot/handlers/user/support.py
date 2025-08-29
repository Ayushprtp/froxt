from ...utils.keyboards import create_keyboard

async def contact_support(query):
    """Show support contact information"""
    await query.edit_message_text(
        text="📞 Help & Support\n\n" \
             "For any questions or issues, please contact our support team:\n\n" \
             "• Email: support@example.com\n" \
             "• Telegram: @support_username\n" \
             "• GitHub: https://github.com/your-repo\n" \
             "• 24/7 Support Available\n\n" \
             "We're here to help you with any OSINT queries!",
        reply_markup=create_keyboard([
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"}]
        ])
    )

async def support_command(update, context):
    """Handle /support command"""
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
    await contact_support(mock_query)