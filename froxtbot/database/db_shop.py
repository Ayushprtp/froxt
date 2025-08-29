import logging
from typing import Dict, Any, List, Optional
from .db_management import DatabaseManager
from ..config import logger
from ..config.shop_items import SHOP_ITEMS_CONFIG

async def get_all_shop_items() -> dict[str, list[Dict[str, Any]]]:
    """Fetches all items from the shop configuration, categorized by type, joining role names."""
    data = await DatabaseManager.load_db()
    items = list(SHOP_ITEMS_CONFIG.values())
    
    # Join role names
    for item in items:
        if item['grants_role_id'] is not None:
            role = data['roles'].get(str(item['grants_role_id']))
            if role:
                item['grants_role'] = role['name']
            else:
                item['grants_role'] = None
        else:
            item['grants_role'] = None
    
    categorized_items = {'Membership': [], 'ZC Pack': [], 'Exclusion Slot': []}
    for item in items:
        if item['type'] in categorized_items:
            categorized_items[item['type']].append(item)
    
    # Sort items by type and price
    for item_type in categorized_items:
        categorized_items[item_type].sort(key=lambda x: (x['type'], x['price_inr']))
    
    return categorized_items

async def get_shop_item_by_id(item_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single shop item by its primary key from config, joining the role name."""
    data = await DatabaseManager.load_db()
    item = SHOP_ITEMS_CONFIG.get(str(item_id))
    
    if item:
        # Create a copy to avoid modifying the original data
        item_copy = item.copy()
        
        # Join role name
        if item_copy['grants_role_id'] is not None:
            role = data['roles'].get(str(item_copy['grants_role_id']))
            if role:
                item_copy['grants_role'] = role['name']
            else:
                item_copy['grants_role'] = None
        else:
            item_copy['grants_role'] = None
            
        return item_copy
    
    return None

async def get_shop_item_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Fetches a single shop item by its name from config."""
    # Search for item by name
    for item in SHOP_ITEMS_CONFIG.values():
        if item['name'] == name:
            # Create a copy to avoid modifying the original data
            return item.copy()
    
    return None

# These functions are no longer needed since shop items are in config, not database
# create_shop_item, update_shop_item_field, and delete_shop_item have been removed

async def create_pending_order(user_id: int, item_id: int) -> int:
    data = await DatabaseManager.load_db()
    
    # Get the next order ID
    next_order_id = data.get('next_order_id', 1)
    
    # Create the new order
    new_order = {
        'order_id': next_order_id,
        'user_id': user_id,
        'item_id': item_id,
        'status': 'pending',
        'created_at': None,  # You might want to add a timestamp here
        'completed_at': None
    }
    
    # Add the new order to the orders dictionary
    data['orders'][str(next_order_id)] = new_order
    
    # Increment next_order_id for the next order
    data['next_order_id'] = next_order_id + 1
    
    # Save the updated database
    await DatabaseManager.save_db(data)
    
    return next_order_id

async def get_order_details(order_id: int) -> Optional[Dict[str, Any]]:
    """Fetches full details for an order, JOINING all necessary tables."""
    data = await DatabaseManager.load_db()
    
    # Convert order_id to string since keys in the JSON are strings
    order_id_str = str(order_id)
    
    # Check if the order exists
    if order_id_str not in data['orders']:
        return None
    
    # Get the order
    order = data['orders'][order_id_str].copy()
    
    # Join user full_name
    user = data['users'].get(str(order['user_id']))
    if user:
        order['full_name'] = user['full_name']
    else:
        order['full_name'] = None
    
    # Join item details from config
    item = SHOP_ITEMS_CONFIG.get(str(order['item_id']))
    if item:
        order['item_name'] = item['name']
        order['type'] = item['type']
        order['price_inr'] = item['price_inr']
        order['grants_role_id'] = item['grants_role_id']
        order['role_duration_days'] = item['role_duration_days']
        order['grants_zc'] = item['grants_zc']
    else:
        order['item_name'] = None
        order['type'] = None
        order['price_inr'] = None
        order['grants_role_id'] = None
        order['role_duration_days'] = None
        order['grants_zc'] = None
    
    return order

async def get_pending_orders() -> List[Dict[str, Any]]:
    """Fetches a summary of all 'pending' orders."""
    data = await DatabaseManager.load_db()
    
    pending_orders = []
    
    # Iterate through all orders
    for order in data['orders'].values():
        # Check if the order is pending
        if order['status'] == 'pending':
            # Create a copy of the order to avoid modifying the original data
            order_copy = order.copy()
            
            # Join user full_name
            user = data['users'].get(str(order['user_id']))
            if user:
                order_copy['full_name'] = user['full_name']
            else:
                order_copy['full_name'] = None
            
            # Join item name from config
            item = SHOP_ITEMS_CONFIG.get(str(order['item_id']))
            if item:
                order_copy['item_name'] = item['name']
            else:
                order_copy['item_name'] = None
                
            pending_orders.append(order_copy)
    
    # Sort orders by creation time (you might need to add a timestamp field)
    pending_orders.sort(key=lambda x: x.get('created_at', ''))
    
    return pending_orders

async def update_order_status(order_id: int, status: str):
    """Updates the status of an order."""
    data = await DatabaseManager.load_db()
    
    # Convert order_id to string since keys in the JSON are strings
    order_id_str = str(order_id)
    
    # Check if the order exists
    if order_id_str not in data['orders']:
        logger.error(f"Attempted to update non-existent order: {order_id}")
        return
    
    # Update the order status
    data['orders'][order_id_str]['status'] = status
    data['orders'][order_id_str]['completed_at'] = None  # You might want to add a timestamp here
    
    # Save the updated database
    await DatabaseManager.save_db(data)
    
    logger.info(f"Updated status of order {order_id} to {status}.")

async def ensure_exclusion_slot_shop_item_exists() -> None:
    """Ensures the 'Exclusion Slot' item exists in the shop config."""
    item_name = "Exclusion Slot"
    existing_item = await get_shop_item_by_name(item_name)
    
    if not existing_item:
        logger.warning(f"Exclusion Slot item not found in config. This should be added to SHOP_ITEMS_CONFIG.")
    else:
        pass  # Item exists, no action needed