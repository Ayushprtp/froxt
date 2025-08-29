from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ...database import db_shop
from ...database.db_users import UserManager
from ...database.db_exclusions import ExclusionManager
from ...utils.keyboards import create_keyboard # Assuming this is the correct import for your keyboard utility

async def show_buy_credits(query):
    """Show credit purchase options"""
    categorized_items = await db_shop.get_all_shop_items()
    
    if not categorized_items["ZC Pack"] and not categorized_items["Membership"]:
        await query.edit_message_text("🛍️ The shop is currently empty.")
        return

    buttons = []
    if categorized_items["ZC Pack"]:
        buttons.append([{"text": "💰 ZC Packs", "callback_data": "shop_category_zc", "style": "info"}])
    if categorized_items["Membership"]:
        buttons.append([{"text": "👑 Memberships", "callback_data": "shop_category_membership", "style": "info"}])
    if categorized_items["Exclusion Slot"]:
        buttons.append([{"text": "🚫 Exclusion Slots", "callback_data": "shop_category_exclusion_slot", "style": "danger"}])

    buttons.append([
        {"text": "🔙 Back to Menu", "callback_data": "back_to_menu", "style": "secondary"}
    ])

    await query.edit_message_text(
        text="🛍️ **Welcome to the Shop!**\n\nSelect a category to browse items.",
        reply_markup=create_keyboard(buttons)
    )

async def show_shop_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split('_')[-1] # 'zc', 'membership', or 'exclusion_slot'

    categorized_items = await db_shop.get_all_shop_items()
    
    display_category_name = category.replace('zc', 'ZC Packs').replace('membership', 'Memberships').replace('exclusion_slot', 'Exclusion Slots')
    items_in_category = categorized_items.get(display_category_name, [])

    if not items_in_category:
        await query.edit_message_text(f"🛍️ No items found in the {display_category_name} category.")
        return

    buttons = []
    for item in items_in_category:
        price_str = f"₹{item['price_inr']:.2f}" if item['price_inr'] is not None else "Not Set"
        buttons.append([
            {"text": f"💎 {item['name']} - {price_str}",
             "callback_data": f"user_shop_select_{item['item_id']}",
             "style": "premium"}
        ])

    buttons.append([
        {"text": "🔙 Back to Shop", "callback_data": "buy_credits", "style": "secondary"}
    ])

    await query.edit_message_text(
        text=f"🛍️ **{display_category_name}**\n\nSelect an item to purchase.",
        reply_markup=create_keyboard(buttons)
    )


async def show_item_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = int(query.data.split('_')[-1])
    
    item = await db_shop.get_shop_item_by_id(item_id)

    if not item:
        await query.edit_message_text("Sorry, this item is no longer available.")
        return

    details = f"**Item:** `{item['name']}`\n"
    
    # Determine price based on item type
    if item['type'] == 'Exclusion Slot':
        cost_zc = 100 # Hardcoded as per requirement
        details += f"**Cost:** `{cost_zc}` ZC\n\n"
        details += f"**Benefit:** Grants you one slot in the exclusion list where you can add a query and a custom message. Queries matching your exclusion will not deduct ZC.\n"
    else:
        price_str = f"₹{item['price_inr']:.2f}" if item['price_inr'] is not None else "Not Set"
        details += f"**Price:** `{price_str}`\n\n"
        if item.get('grants_zc'):
            details += f"**Benefit:** Adds `{item['grants_zc']}` credits to your balance.\n"
        if item.get('grants_role'):
            details += f"**Role:** Grants `{item['grants_role']}` role.\n"
        if item.get('role_duration_days'):
            details += f"**Duration:** `{item['role_duration_days']}` days.\n"

    text = (f"**Confirmation**\n\n{details}\n\n")
    
    if item['type'] == 'Exclusion Slot':
        text += "Are you sure you want to purchase this exclusion slot?"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Purchase (100 ZC)", callback_data=f"user_shop_confirm_exclusion_slot_{item['item_id']}")],
            [InlineKeyboardButton("❌ No, Cancel", callback_data="buy_credits")]
        ])
    elif item['type'] == 'Membership':
        # Membership roles have duration options
        role_id = item['grants_role_id']
        role_details = await UserManager.get_role_by_id(role_id)
        role_name = role_details.get('name', 'N/A') if role_details else 'N/A'
        zc_per_day = role_details.get('grants_zc_per_day', 0) if role_details else 0

        duration_options = {
            "2_weeks": {"days": 14, "cost_multiplier": 2},
            "4_weeks": {"days": 28, "cost_multiplier": 3.5}, # Slightly discounted
            "8_weeks": {"days": 56, "cost_multiplier": 6},   # More discounted
            "12_weeks": {"days": 84, "cost_multiplier": 8}   # Even more discounted
        }
        
        buttons = []
        for key, value in duration_options.items():
            duration_text = key.replace('_', ' ').title()
            cost = int(zc_per_day * value["days"] * value["cost_multiplier"]) # Correct cost calculation
            buttons.append([InlineKeyboardButton(f"{duration_text} ({cost} ZC)", callback_data=f"user_shop_confirm_membership_{item_id}_{value['days']}")])
        
        buttons.append([InlineKeyboardButton("⬅️ Back to Memberships", callback_data="shop_category_membership")])

        text = (
                f"**Purchase {role_name} Role**\n\n"
                f"Daily ZC Grant: `{zc_per_day}` ZC\n"
                f"Cooldown: `{role_details.get('cooldown', 'N/A')}` seconds\n\n"
                "Select duration:")
        keyboard = InlineKeyboardMarkup(buttons)

    else:
        text += "Pressing confirm below will create your order."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm Purchase Request", callback_data=f"user_shop_confirm_{item_id}")],
            [InlineKeyboardButton("⬅️ Back to Shop", callback_data="buy_credits")]
        ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')


async def handle_and_redirect_purchase_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    parts = query.data.split('_')
    action_type = parts[2] # 'exclusion' or 'membership' or regular item
    item_id = int(parts[-1])
    item = await db_shop.get_shop_item_by_id(item_id)

    if not item:
        await query.edit_message_text("An error occurred. Please try again.")
        return

    if action_type == 'exclusion_slot':
        cost_zc = 100 # Hardcoded as per requirement
        user_credits = await UserManager.get_user_credits(user_id)

        if user_credits < cost_zc:
            await query.answer("❌ Insufficient ZC to purchase this slot.", show_alert=True)
            await query.edit_message_text(
                text=f"❌ Insufficient ZC\n\n"
                     f"You need {cost_zc} ZC to purchase an Exclusion Slot.\n"
                     f"Your balance: {user_credits} ZC\n\n"
                     "Please buy more ZC packs.",
                reply_markup=create_keyboard([
                    [{"text": "💳 Buy ZC Packs", "callback_data": "shop_category_zc", "style": "success"}],
                    [{"text": "🔙 Back to Shop", "callback_data": "buy_credits", "style": "secondary"}]
                ])
            )
            return
        
        # Deduct credits and purchase slot
        await UserManager.deduct_credits_raw(user_id, cost_zc) # Deduct directly
        exclusion_no = await ExclusionManager.purchase_exclusion_slot(user_id)

        if exclusion_no:
            await query.edit_message_text(
                text=f"✅ Exclusion Slot Purchased!\n\n"
                     f"You have successfully purchased an exclusion slot for {cost_zc} ZC.\n"
                     f"Your new balance: {user_credits - cost_zc} ZC.\n\n"
                     f"You can now add your excluded query and message to this slot (ID: `{exclusion_no}`).",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "📝 Manage My Exclusions", "callback_data": "user_exclusion_management", "style": "primary"}],
                    [{"text": "🔙 Back to Shop", "callback_data": "buy_credits", "style": "secondary"}]
                ])
            )
        else:
            await query.edit_message_text(
                text="❌ Failed to purchase exclusion slot. An error occurred.",
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": f"user_shop_select_{item_id}", "style": "primary"}],
                    [{"text": "🔙 Back to Shop", "callback_data": "buy_credits", "style": "secondary"}]
                ])
            )
        await query.answer() # Answer the callback query
        return
    
    elif action_type == 'membership':
        duration_days = int(parts[-1])
        role_id = item['grants_role_id']
        role_details = await UserManager.get_role_by_id(role_id)
        zc_per_day = role_details.get('grants_zc_per_day', 0) if role_details else 0

        # Recalculate cost based on duration options (must match show_item_confirmation)
        duration_options = {
            14: {"cost_multiplier": 2},
            28: {"cost_multiplier": 3.5},
            56: {"cost_multiplier": 6},
            84: {"cost_multiplier": 8}
        }
        cost_multiplier = duration_options.get(duration_days, {}).get("cost_multiplier", 1)
        total_cost_zc = int(zc_per_day * duration_days * cost_multiplier) # Correct cost calculation

        user_credits = await UserManager.get_user_credits(user_id)

        if user_credits < total_cost_zc:
            await query.answer("❌ Insufficient ZC to purchase this role.", show_alert=True)
            await query.edit_message_text(
                text=f"❌ Insufficient ZC\n\n"
                     f"You need {total_cost_zc} ZC to purchase this role for {duration_days} days.\n"
                     f"Your balance: {user_credits} ZC\n\n"
                     "Please buy more ZC packs.",
                reply_markup=create_keyboard([
                    [{"text": "💳 Buy ZC Packs", "callback_data": "shop_category_zc", "style": "success"}],
                    [{"text": "🔙 Back to Memberships", "callback_data": "shop_category_membership", "style": "secondary"}]
                ])
            )
            return
        
        # Deduct credits and promote user
        await UserManager.deduct_credits_raw(user_id, total_cost_zc)
        success = await UserManager.promote_user(user_id, role_id, duration_days)

        if success:
            await query.edit_message_text(
                text=f"✅ Role Purchased!\n\n"
                     f"You have successfully purchased the `{item['name']}` role for {duration_days} days for {total_cost_zc} ZC.\n"
                     f"Your new balance: {user_credits - total_cost_zc} ZC.\n"
                     f"Your role will expire on: `{(datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')}`\n\n"
                     "Enjoy your new benefits!",
                parse_mode='Markdown',
                reply_markup=create_keyboard([
                    [{"text": "📊 My Dashboard", "callback_data": "my_dashboard", "style": "primary"}],
                    [{"text": "🔙 Back to Shop", "callback_data": "buy_credits", "style": "secondary"}]
                ])
            )
        else:
            await query.edit_message_text(
                text="❌ Failed to purchase role. An error occurred.",
                reply_markup=create_keyboard([
                    [{"text": "↩️ Try Again", "callback_data": f"user_shop_select_{item_id}", "style": "primary"}],
                    [{"text": "🔙 Back to Memberships", "callback_data": "shop_category_membership", "style": "secondary"}]
                ])
            )
        await query.answer()
        return

    # Existing logic for other shop items (INR purchases)
    await query.answer("Creating your order...")

    order_id = await db_shop.create_pending_order(user_id, item_id)

    prefilled_message = (
        f"Order Confirmation (Order #{order_id})\n"
        f"---------------------------\n"
        f"Item: {item['name']}\n"
        f"Price: ₹{item['price_inr']:.2f}\n"
        f"User Name: {query.from_user.full_name}\n"
        f"User ID: {query.from_user.id}"
    )
    
    await query.edit_message_text(
        text=f"✅ **Order #{order_id} created!**\n\nPlease contact support with the following information to complete your purchase:\n\n```\n{prefilled_message}\n```",
        parse_mode='Markdown',
        reply_markup=create_keyboard([
            [{"text": "📞 Contact Support", "callback_data": "contact_support", "style": "info"}],
            [{"text": "🔙 Back to Shop", "callback_data": "buy_credits", "style": "secondary"}]
        ])
    )

async def buy_command(update, context):
    """Handle /buy command"""
    # This function will be called from the main bot file, so it needs to import check_force_join
    from ...utils.join_checker import check_force_join
    if not await check_force_join(update, context):
        return
    
    class MockQuery:
        def __init__(self, user, message):
            self.from_user = user
            self.message = message
            
        async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
            await self.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        
        async def answer(self, text=None, show_alert=False):
            pass # Mock answer for callback query

    mock_query = MockQuery(update.effective_user, update.message)
    await show_buy_credits(mock_query)