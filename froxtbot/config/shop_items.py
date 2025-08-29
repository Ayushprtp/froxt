from typing import Dict, Any

# Shop Items Configuration
# This configuration defines all items available in the bot's shop
# Each item has the following properties:
# - item_id: Unique identifier for the item
# - type: Type of item (ZC Pack, Membership, Exclusion Slot)
# - name: Name of the item
# - description: Description of the item
# - price_inr: Price in Indian Rupees
# - grants_zc: Number of ZC credits granted (if applicable)
# - grants_role_id: Role ID granted (if applicable)
# - role_duration_days: Duration of the role in days (if applicable)

SHOP_ITEMS_CONFIG: Dict[str, Dict[str, Any]] = {
    "1": {
        "item_id": 1,
        "type": "ZC Pack",
        "name": "10 Credits",
        "description": "Adds 10 credits to your balance.",
        "price_inr": 1.99,
        "grants_zc": 10,
        "grants_role_id": None,
        "role_duration_days": None
    },
    "2": {
        "item_id": 2,
        "type": "ZC Pack",
        "name": "25 Credits",
        "description": "Adds 25 credits to your balance.",
        "price_inr": 4.49,
        "grants_zc": 25,
        "grants_role_id": None,
        "role_duration_days": None
    },
    "3": {
        "item_id": 3,
        "type": "ZC Pack",
        "name": "50 Credits",
        "description": "Adds 50 credits to your balance.",
        "price_inr": 7.99,
        "grants_zc": 50,
        "grants_role_id": None,
        "role_duration_days": None
    },
    "4": {
        "item_id": 4,
        "type": "ZC Pack",
        "name": "100 Credits",
        "description": "Adds 100 credits to your balance.",
        "price_inr": 14.99,
        "grants_zc": 100,
        "grants_role_id": None,
        "role_duration_days": None
    },
    "5": {
        "item_id": 5,
        "type": "ZC Pack",
        "name": "500 Credits (Demo)",
        "description": "Adds 500 credits to your balance (Demo).",
        "price_inr": 0.0,
        "grants_zc": 500,
        "grants_role_id": None,
        "role_duration_days": None
    },
    "6": {
        "item_id": 6,
        "type": "ZC Pack",
        "name": "1000 Credits (Demo)",
        "description": "Adds 1000 credits to your balance (Demo).",
        "price_inr": 0.0,
        "grants_zc": 1000,
        "grants_role_id": None,
        "role_duration_days": None
    },
    "7": {
        "item_id": 7,
        "type": "Membership",
        "name": "Basic Role",
        "description": "Grants Basic role with 60s cooldown and 10 ZC/day.",
        "price_inr": 0.0,
        "grants_zc": None,
        "grants_role_id": 2,
        "role_duration_days": None
    },
    "8": {
        "item_id": 8,
        "type": "Membership",
        "name": "Pro Role",
        "description": "Grants Pro role with 15s cooldown and 25 ZC/day.",
        "price_inr": 0.0,
        "grants_zc": None,
        "grants_role_id": 3,
        "role_duration_days": None
    },
    "9": {
        "item_id": 9,
        "type": "Membership",
        "name": "Elite Role",
        "description": "Grants Elite role with 3s cooldown and 50 ZC/day.",
        "price_inr": 0.0,
        "grants_zc": None,
        "grants_role_id": 4,
        "role_duration_days": None
    },
    "10": {
        "item_id": 10,
        "type": "Exclusion Slot",
        "name": "Exclusion Slot",
        "description": "",
        "price_inr": 0.0,
        "grants_zc": None,
        "grants_role_id": None,
        "role_duration_days": None
    }
}