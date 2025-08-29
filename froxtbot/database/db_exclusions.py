import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from .db_management import DatabaseManager

logger = logging.getLogger(__name__)

class ExclusionManager:
    @staticmethod
    async def add_exclusion(user_id: int, value: str, message: str, added_by_admin: bool = False) -> Optional[int]:
        try:
            db = await DatabaseManager.load_db()
            
            # Check for existing exclusion with the same value
            for ex_id, ex_data in db.get("exclusions", {}).items():
                if ex_data["value"].lower() == value.lower():
                    logger.warning(f"Attempted to add duplicate exclusion value: {value}")
                    return None # Value already exists

            next_id = db.get("next_exclusion_no", 1)
            
            db.setdefault("exclusions", {})[str(next_id)] = {
                "exclusion_no": next_id,
                "value": value,
                "message": message,
                "added_by": user_id,
                "added_by_admin": added_by_admin,
                "timestamp": datetime.now().isoformat(),
                "slot_owner": user_id if not added_by_admin else None # For user-purchased slots
            }
            db["next_exclusion_no"] = next_id + 1
            
            await DatabaseManager.save_db(db)
            logger.info(f"Added exclusion '{value}' by user {user_id} (admin: {added_by_admin}) with ID {next_id}.")
            return next_id
        except Exception as e:
            logger.error(f"Error adding exclusion for user {user_id}: {e}")
            return None

    @staticmethod
    async def get_exclusion(value: str) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            for ex_id, ex_data in db.get("exclusions", {}).items():
                if ex_data["value"].lower() == value.lower():
                    return ex_data
            return None
        except Exception as e:
            logger.error(f"Error getting exclusion for value '{value}': {e}")
            return None

    @staticmethod
    async def get_exclusion_by_id(exclusion_no: int) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            return db.get("exclusions", {}).get(str(exclusion_no))
        except Exception as e:
            logger.error(f"Error getting exclusion by ID {exclusion_no}: {e}")
            return None

    @staticmethod
    async def get_user_exclusions(user_id: int) -> List[Dict]:
        try:
            db = await DatabaseManager.load_db()
            return [ex_data for ex_data in db.get("exclusions", {}).values() if ex_data.get("slot_owner") == user_id]
        except Exception as e:
            logger.error(f"Error getting user exclusions for user {user_id}: {e}")
            return []

    @staticmethod
    async def get_all_exclusions() -> List[Dict]:
        try:
            db = await DatabaseManager.load_db()
            return list(db.get("exclusions", {}).values())
        except Exception as e:
            logger.error(f"Error getting all exclusions: {e}")
            return []

    @staticmethod
    async def update_exclusion(exclusion_no: int, new_value: str, new_message: str, user_id: int, is_admin: bool) -> bool:
        try:
            db = await DatabaseManager.load_db()
            exclusion = db.get("exclusions", {}).get(str(exclusion_no))
            user = db["users"].get(str(user_id))
            
            if not exclusion or not user:
                logger.warning(f"Attempted to update non-existent exclusion {exclusion_no} or user {user_id} not found.")
                return False
            
            # Check ownership for non-admin users
            if not is_admin and exclusion.get("slot_owner") != user_id:
                logger.warning(f"User {user_id} attempted to update exclusion {exclusion_no} without ownership.")
                return False
                
            # Check for duplicate value if changing
            if new_value.lower() != exclusion["value"].lower():
                for ex_id, ex_data in db.get("exclusions", {}).items():
                    if ex_data["value"].lower() == new_value.lower() and int(ex_id) != exclusion_no:
                        logger.warning(f"Attempted to update exclusion {exclusion_no} to duplicate value: {new_value}")
                        return False

            # Deduct ZC for user edits
            if not is_admin:
                edit_cost = 5
                if user["credits"] < edit_cost:
                    logger.warning(f"User {user_id} attempted to edit exclusion {exclusion_no} but has insufficient credits.")
                    return False
                user["credits"] -= edit_cost
                logger.info(f"User {user_id} paid {edit_cost} ZC to edit exclusion {exclusion_no}.")

            exclusion["value"] = new_value
            exclusion["message"] = new_message
            exclusion["timestamp"] = datetime.now().isoformat() # Update timestamp on edit
            
            await DatabaseManager.save_db(db)
            logger.info(f"Updated exclusion {exclusion_no} to '{new_value}' by user {user_id} (admin: {is_admin}).")
            return True
        except Exception as e:
            logger.error(f"Error updating exclusion {exclusion_no} by user {user_id}: {e}")
            return False

    @staticmethod
    async def delete_exclusion(exclusion_no: int, user_id: int, is_admin: bool) -> bool:
        try:
            db = await DatabaseManager.load_db()
            exclusion = db.get("exclusions", {}).get(str(exclusion_no))
            
            if not exclusion:
                logger.warning(f"Attempted to delete non-existent exclusion: {exclusion_no}")
                return False
            
            # Check ownership for non-admin users
            if not is_admin and exclusion.get("slot_owner") != user_id:
                logger.warning(f"User {user_id} attempted to delete exclusion {exclusion_no} without ownership.")
                return False

            # Instead of deleting, mark as placeholder and clear content
            exclusion["value"] = ""
            exclusion["message"] = ""
            exclusion["is_placeholder"] = True
            exclusion["timestamp"] = datetime.now().isoformat()
            
            await DatabaseManager.save_db(db)
            logger.info(f"User {user_id} cleared exclusion slot {exclusion_no} (admin: {is_admin}).")
            return True
        except Exception as e:
            logger.error(f"Error deleting exclusion {exclusion_no} by user {user_id}: {e}")
            return False

    @staticmethod
    async def get_next_exclusion_no() -> int:
        try:
            db = await DatabaseManager.load_db()
            return db.get("next_exclusion_no", 1)
        except Exception as e:
            logger.error(f"Error getting next exclusion number: {e}")
            return 1

    @staticmethod
    async def get_user_exclusion_slots_count(user_id: int) -> int:
        try:
            db = await DatabaseManager.load_db()
            return sum(1 for ex_data in db.get("exclusions", {}).values() if ex_data.get("slot_owner") == user_id)
        except Exception as e:
            logger.error(f"Error getting user exclusion slots count for user {user_id}: {e}")
            return 0

    @staticmethod
    async def purchase_exclusion_slot(user_id: int) -> Optional[int]:
        try:
            db = await DatabaseManager.load_db()
            user = db["users"].get(str(user_id))
            if not user:
                return None

            slot_cost = 100 # ZC
            if user["credits"] < slot_cost:
                return None

            user["credits"] -= slot_cost
            
            # Create a placeholder exclusion entry to reserve the slot
            next_id = db.get("next_exclusion_no", 1)
            db.setdefault("exclusions", {})[str(next_id)] = {
                "exclusion_no": next_id,
                "value": "", # Placeholder
                "message": "", # Placeholder
                "added_by": user_id,
                "added_by_admin": False,
                "timestamp": datetime.now().isoformat(),
                "slot_owner": user_id,
                "is_placeholder": True # Mark as placeholder
            }
            db["next_exclusion_no"] = next_id + 1

            await DatabaseManager.save_db(db)
            logger.info(f"User {user_id} purchased exclusion slot {next_id} for {slot_cost} ZC.")
            return next_id
        except Exception as e:
            logger.error(f"Error purchasing exclusion slot for user {user_id}: {e}")
            return None

    @staticmethod
    async def fill_exclusion_slot(exclusion_no: int, user_id: int, value: str, message: str) -> bool:
        try:
            db = await DatabaseManager.load_db()
            exclusion = db.get("exclusions", {}).get(str(exclusion_no))

            if not exclusion or exclusion.get("slot_owner") != user_id or not exclusion.get("is_placeholder"):
                logger.warning(f"Attempted to fill non-existent or unowned placeholder slot {exclusion_no} by user {user_id}.")
                return False
            
            # Check for duplicate value
            for ex_id, ex_data in db.get("exclusions", {}).items():
                if ex_data["value"].lower() == value.lower() and int(ex_id) != exclusion_no:
                    logger.warning(f"Attempted to fill slot {exclusion_no} with duplicate value: {value}")
                    return False

            exclusion["value"] = value
            exclusion["message"] = message
            exclusion["is_placeholder"] = False
            exclusion["timestamp"] = datetime.now().isoformat()

            await DatabaseManager.save_db(db)
            logger.info(f"User {user_id} filled exclusion slot {exclusion_no} with '{value}'.")
            return True
        except Exception as e:
            logger.error(f"Error filling exclusion slot {exclusion_no} for user {user_id}: {e}")
            return False
