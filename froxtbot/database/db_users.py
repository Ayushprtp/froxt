from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from .db_management import DatabaseManager
from ..config.services import SERVICES_CONFIG
from ..config import logger

class UserManager:
    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            user_data = db["users"].get(str(user_id))
            if user_data:
                # Ensure all required fields exist
                required_fields = {
                    "id": user_id,
                    "username": None,
                    "credits": 0.0,
                    "joined_at": datetime.now().isoformat(),
                    "banned": False,
                    "referrals": [],
                    "last_active": datetime.now().isoformat(),
                    "total_requests": 0,
                    "daily_requests": 0,
                    "last_request_date": datetime.now().date().isoformat(),
                    "role_id": 1, # Default to 'Free User' role
                    "cooldown_until": None,
                    "role_expiry_date": None, # New field for role expiry
                    "last_zc_grant_date": None, # New field for daily ZC grants
                }
                for field, default in required_fields.items():
                    if field not in user_data:
                        user_data[field] = default
                
                # Check for role expiry
                if user_data.get("role_expiry_date"):
                    try:
                        expiry_date = datetime.fromisoformat(user_data["role_expiry_date"])
                        if datetime.now() > expiry_date:
                            user_data["role_id"] = 1 # Revert to Free User
                            user_data["role_expiry_date"] = None
                            user_data["last_zc_grant_date"] = None # Reset ZC grant date
                            logger.info(f"User {user_id}'s role expired and reverted to Free User.")
                            await DatabaseManager.save_db(db) # Save changes immediately
                    except ValueError:
                        logger.error(f"Invalid role_expiry_date for user {user_id}: {user_data['role_expiry_date']}")
                        user_data["role_expiry_date"] = None # Clear invalid date

                # Check for daily ZC grant
                if user_data.get("role_id") != 1: # Only for non-Free users
                    user_role = db["roles"].get(str(user_data["role_id"]))
                    if user_role and user_role.get("grants_zc_per_day", 0) > 0:
                        today = datetime.now().date()
                        last_grant_date_str = user_data.get("last_zc_grant_date")
                        last_grant_date = None
                        if last_grant_date_str:
                            try:
                                last_grant_date = datetime.fromisoformat(last_grant_date_str).date()
                            except ValueError:
                                logger.error(f"Invalid last_zc_grant_date for user {user_id}: {last_grant_date_str}")
                                user_data["last_zc_grant_date"] = None

                        if not last_grant_date or last_grant_date < today:
                            zc_to_grant = user_role["grants_zc_per_day"]
                            user_data["credits"] += zc_to_grant
                            user_data["last_zc_grant_date"] = today.isoformat()
                            if "stats" in db and "total_credits_distributed" in db["stats"]:
                                db["stats"]["total_credits_distributed"] += zc_to_grant
                            else:
                                db["stats"]["total_credits_distributed"] = zc_to_grant
                            logger.info(f"User {user_id} granted {zc_to_grant} ZC for role {user_role['name']}.")
                            await DatabaseManager.save_db(db) # Save changes immediately
            return user_data
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    @staticmethod
    async def create_user(user_id: int, username: Optional[str] = None, referrer_id: Optional[int] = None) -> Dict:
        try:
            db = await DatabaseManager.load_db()
            
            if str(user_id) not in db["users"]:
                welcome_bonus = db["settings"].get("welcome_bonus", 2.0)
                user_data = {
                    "id": user_id,
                    "username": username,
                    "credits": welcome_bonus,
                    "joined_at": datetime.now().isoformat(),
                    "referrer": referrer_id,
                    "referrals": [],
                    "banned": False,
                    "last_active": datetime.now().isoformat(),
                    "total_requests": 0,
                    "daily_requests": 0,
                    "last_request_date": datetime.now().date().isoformat(),
                    "role_id": 1, # Assign default 'Free User' role
                    "cooldown_until": None,
                    "role_expiry_date": None,
                    "last_zc_grant_date": None,
                }
                db["users"][str(user_id)] = user_data

                # Handle referral bonus
                if referrer_id and str(referrer_id) in db["users"]:
                    referral_bonus = db["settings"]["referral_bonus"]
                    db["users"][str(referrer_id)]["credits"] += referral_bonus
                    db["users"][str(referrer_id)]["referrals"].append(user_id)
                    db["users"][str(user_id)]["credits"] += referral_bonus
                    db["stats"]["total_credits_distributed"] += referral_bonus * 2

                # Update peak users
                current_users = len(db["users"])
                if current_users > db["stats"].get("peak_users", 0):
                    db["stats"]["peak_users"] = current_users

                await DatabaseManager.save_db(db)
                return user_data
            return db["users"][str(user_id)]
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            # Return a default user structure in case of error
            return {
                "id": user_id,
                "username": username,
                "credits": 0.0,
                "joined_at": datetime.now().isoformat(),
                "banned": False,
                "referrals": [],
                "last_active": datetime.now().isoformat(),
                "total_requests": 0,
                "daily_requests": 0,
                "last_request_date": datetime.now().date().isoformat(),
                "role_id": 1,
                "cooldown_until": None,
                "role_expiry_date": None,
                "last_zc_grant_date": None,
            }

    @staticmethod
    async def get_user_role(user_id: int) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            user = db["users"].get(str(user_id))
            if user and "role_id" in user:
                role_id = str(user["role_id"])
                return db["roles"].get(role_id)
            return None
        except Exception as e:
            logger.error(f"Error getting user role for {user_id}: {e}")
            return None

    @staticmethod
    async def update_user_role(user_id: int, role_id: int) -> bool:
        try:
            db = await DatabaseManager.load_db()
            if str(user_id) in db["users"] and str(role_id) in db["roles"]:
                db["users"][str(user_id)]["role_id"] = role_id
                db["users"][str(user_id)]["last_active"] = datetime.now().isoformat()
                return await DatabaseManager.save_db(db)
            return False
        except Exception as e:
            logger.error(f"Error updating user role for {user_id}: {e}")
            return False

    @staticmethod
    async def update_user_credits(user_id: int, amount: float, reason: str = "manual") -> bool:
        try:
            db = await DatabaseManager.load_db()
            if str(user_id) in db["users"]:
                new_balance = db["users"][str(user_id)]["credits"] + amount
                if new_balance >= 0:
                    db["users"][str(user_id)]["credits"] = round(new_balance, 2)
                    db["users"][str(user_id)]["last_active"] = datetime.now().isoformat()
                    
                    if amount > 0:
                        db["stats"]["total_credits_distributed"] += amount
                        
                    return await DatabaseManager.save_db(db)
            return False
        except Exception as e:
            logger.error(f"Error updating user credits for {user_id}: {e}")
            return False

    @staticmethod
    async def check_rate_limit(user_id: int) -> Tuple[bool, Optional[str]]:
        try:
            db = await DatabaseManager.load_db()
            user = db["users"].get(str(user_id))
            
            if not user:
                return False, "User not found"
            
            # Check cooldown
            if user.get("cooldown_until"):
                try:
                    cooldown_until = datetime.fromisoformat(user["cooldown_until"])
                    if datetime.now() < cooldown_until:
                        remaining = (cooldown_until - datetime.now()).seconds
                        return False, f"Cooldown active. Try again in {remaining} seconds."
                except:
                    pass
            
            # Reset daily counter if new day
            today = datetime.now().date().isoformat()
            if user.get("last_request_date") != today:
                user["daily_requests"] = 0
                user["last_request_date"] = today
            
            # Get user's role and its rate limit
            user_role = await UserManager.get_user_role(user_id)
            rate_limit = user_role.get("rate_limit", db["settings"].get("max_requests_per_day", 100)) if user_role else db["settings"].get("max_requests_per_day", 100)

            # Check daily limit based on role
            if user.get("daily_requests", 0) >= rate_limit:
                return False, f"Daily limit of {rate_limit} requests reached for your role. Upgrade your role for more access!"
            
            return True, None
        except Exception as e:
            logger.error(f"Error checking rate limit for user {user_id}: {e}")
            return False, "An error occurred while checking your rate limit. Please try again later."

    @staticmethod
    async def has_enough_credits(user_id: int, service: str) -> bool:
        try:
            user = await UserManager.get_user(user_id)
            if not user or user.get("banned", False):
                return False
            
            service_info = SERVICES_CONFIG.get(service, {})
            cost = service_info.get("servicecost", 0)
            return user.get("credits", 0) >= cost
        except Exception as e:
            logger.error(f"Error checking credits for user {user_id} and service {service}: {e}")
            return False

    @staticmethod
    async def get_user_credits(user_id: int) -> float:
        try:
            db = await DatabaseManager.load_db()
            user = db["users"].get(str(user_id))
            return user.get("credits", 0.0) if user else 0.0
        except Exception as e:
            logger.error(f"Error getting user credits for {user_id}: {e}")
            return 0.0

    @staticmethod
    async def deduct_credits_raw(user_id: int, amount: float, reason: str = "manual") -> bool:
        try:
            db = await DatabaseManager.load_db()
            if str(user_id) in db["users"]:
                user = db["users"][str(user_id)]
                if user["credits"] >= amount:
                    user["credits"] -= amount
                    user["last_active"] = datetime.now().isoformat()
                    await DatabaseManager.save_db(db)
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deducting credits for user {user_id}: {e}")
            return False

    @staticmethod
    async def deduct_credits(user_id: int, service: str, query_text: str = "N/A") -> bool:
        try:
            service_info = SERVICES_CONFIG.get(service, {})
            cost = service_info.get("servicecost", 0)
            
            db = await DatabaseManager.load_db()
            if str(user_id) in db["users"]:
                db["users"][str(user_id)]["daily_requests"] = db["users"][str(user_id)].get("daily_requests", 0) + 1
                db["users"][str(user_id)]["total_requests"] = db["users"][str(user_id)].get("total_requests", 0) + 1
                db["stats"]["total_requests"] = db["stats"].get("total_requests", 0) + 1
                db["stats"]["daily_requests"] = db["stats"].get("daily_requests", 0) + 1
                
                # Update popular tools analytics
                if "analytics" not in db:
                    db["analytics"] = {"popular_tools": {}}
                if "popular_tools" not in db["analytics"]:
                    db["analytics"]["popular_tools"] = {}
                
                db["analytics"]["popular_tools"][service] = db["analytics"]["popular_tools"].get(service, 0) + 1
                
                # Set cooldown
                user_role = await UserManager.get_user_role(user_id)
                cooldown_seconds = user_role.get("cooldown", db["settings"].get("cooldown_period", 10)) if user_role else db["settings"].get("cooldown_period", 10)
                db["users"][str(user_id)]["cooldown_until"] = (datetime.now() + timedelta(seconds=cooldown_seconds)).isoformat()

                # Log query to history
                db["query_history"].append({
                    "user_id": user_id,
                    "service_name": service,
                    "query_text": query_text,
                    "timestamp": datetime.now().isoformat()
                })
                # Keep history to a reasonable size (e.g., last 1000 queries)
                db["query_history"] = db["query_history"][-1000:]

                await DatabaseManager.save_db(db)
                if cost > 0:
                    return await UserManager.update_user_credits(user_id, -cost, f"used_{service}")
            return True
        except Exception as e:
            logger.error(f"Error deducting credits for user {user_id} and service {service}: {e}")
            return False

    @staticmethod
    async def get_users_paginated(page: int = 1, limit: int = 10) -> list[Dict]:
        try:
            db = await DatabaseManager.load_db()
            users = list(db["users"].values())
            users.sort(key=lambda u: u.get("joined_at", ""), reverse=True) # Sort by join date
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_users = users[start_index:end_index]
            
            # Enrich user data with role name
            for user in paginated_users:
                role = db["roles"].get(str(user.get("role_id", 1)))
                user["role_name"] = role["name"] if role else "N/A"
            return paginated_users
        except Exception as e:
            logger.error(f"Error getting paginated users: {e}")
            return []

    @staticmethod
    async def get_user_count() -> int:
        try:
            db = await DatabaseManager.load_db()
            return len(db["users"])
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0

    @staticmethod
    async def get_user_profile(user_id: int) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            user_data = db["users"].get(str(user_id))
            if user_data:
                role = db["roles"].get(str(user_data.get("role_id", 1)))
                user_data["role"] = role["name"] if role else "N/A"
                user_data["zc_balance"] = user_data.get("credits", 0.0)
                user_data["is_banned"] = user_data.get("banned", False)
                user_data["full_name"] = user_data.get("username", f"User {user_id}") # Placeholder for full_name
            return user_data
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None

    @staticmethod
    async def search_user(query: str) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            for user_id, user_data in db["users"].items():
                if (query.isdigit() and user_id == query) or \
                   (user_data.get('username') and query.lower() in user_data['username'].lower()):
                    return await UserManager.get_user_profile(int(user_id))
            return None
        except Exception as e:
            logger.error(f"Error searching user with query '{query}': {e}")
            return None

    @staticmethod
    async def get_all_roles() -> list[Dict]:
        try:
            db = await DatabaseManager.load_db()
            return list(db["roles"].values())
        except Exception as e:
            logger.error(f"Error getting all roles: {e}")
            return []

    @staticmethod
    async def get_role_by_id(role_id: int) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            return db["roles"].get(str(role_id))
        except Exception as e:
            logger.error(f"Error getting role by ID {role_id}: {e}")
            return None

    @staticmethod
    async def get_role_by_name(role_name: str) -> Optional[Dict]:
        try:
            db = await DatabaseManager.load_db()
            for role_id, role_data in db["roles"].items():
                if role_data.get("name") == role_name:
                    return role_data
            return None
        except Exception as e:
            logger.error(f"Error getting role by name '{role_name}': {e}")
            return None

    @staticmethod
    async def update_user_balance(user_id: int, new_balance: float) -> bool:
        try:
            db = await DatabaseManager.load_db()
            if str(user_id) in db["users"]:
                db["users"][str(user_id)]["credits"] = round(new_balance, 2)
                db["users"][str(user_id)]["last_active"] = datetime.now().isoformat()
                return await DatabaseManager.save_db(db)
            return False
        except Exception as e:
            logger.error(f"Error updating user balance for {user_id}: {e}")
            return False

    @staticmethod
    async def set_user_banned_status(user_id: int, banned: bool) -> bool:
        try:
            db = await DatabaseManager.load_db()
            if str(user_id) in db["users"]:
                db["users"][str(user_id)]["banned"] = banned
                db["users"][str(user_id)]["last_active"] = datetime.now().isoformat()
                return await DatabaseManager.save_db(db)
            return False
        except Exception as e:
            logger.error(f"Error setting user banned status for {user_id}: {e}")
            return False

    @staticmethod
    async def get_all_user_ids() -> List[int]:
        try:
            db = await DatabaseManager.load_db()
            return [int(user_id) for user_id in db["users"].keys()]
        except Exception as e:
            logger.error(f"Error getting all user IDs: {e}")
            return []

    @staticmethod
    async def promote_user(user_id: int, role_id: int, duration_days: Optional[int] = None) -> bool:
        try:
            db = await DatabaseManager.load_db()
            if str(user_id) in db["users"] and str(role_id) in db["roles"]:
                user = db["users"][str(user_id)]
                user["role_id"] = role_id
                if duration_days is not None and duration_days > 0:
                    user["role_expiry_date"] = (datetime.now() + timedelta(days=duration_days)).isoformat()
                else:
                    user["role_expiry_date"] = None # Permanent role
                user["last_active"] = datetime.now().isoformat()
                return await DatabaseManager.save_db(db)
            return False
        except Exception as e:
            logger.error(f"Error promoting user {user_id} to role {role_id}: {e}")
            return False
