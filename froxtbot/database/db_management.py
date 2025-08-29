import os
import json
import asyncio
from datetime import datetime
from typing import Dict
from ..config import DEFAULT_API_CONFIG, DATABASE_FILE, BACKUP_FILE, logger

class DatabaseManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def initialize_db():
        if not os.path.exists(DATABASE_FILE):
            default_data = {
                "users": {},
                "settings": {
                    "referral_bonus": 0.5,
                    "welcome_bonus": 2.0,
                    "maintenance_mode": False,
                    "max_requests_per_day": 100,
                    "cooldown_period": 10,
                },
                "stats": {
                    "total_requests": 0,
                    "daily_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "last_reset": datetime.now().isoformat(),
                    "peak_users": 0,
                    "total_credits_distributed": 0,
                },
                "analytics": {
                    "popular_tools": {},
                    "error_logs": [],
                    "daily_stats": {}
                },
                "orders": {},
                "query_history": [], # New field for query history
                "roles": {
                    "1": {"role_id": 1, "name": "Free User", "rate_limit": 100, "cooldown": 60, "grants_zc_per_day": 0},
                    "2": {"role_id": 2, "name": "Basic", "rate_limit": 200, "cooldown": 60, "grants_zc_per_day": 10},
                    "3": {"role_id": 3, "name": "Pro", "rate_limit": 500, "cooldown": 15, "grants_zc_per_day": 25},
                    "4": {"role_id": 4, "name": "Elite", "rate_limit": 1000, "cooldown": 3, "grants_zc_per_day": 50},
                    "5": {"role_id": 5, "name": "Admin", "rate_limit": 99999, "cooldown": 0, "grants_zc_per_day": 0}
                },
                "version": "2.3" # Increment version
            }
            with open(DATABASE_FILE, "w") as f:
                json.dump(default_data, f, indent=4)

    @staticmethod
    async def load_db() -> Dict:
        async with DatabaseManager._lock:
            try:
                with open(DATABASE_FILE, "r") as f:
                    data = json.load(f)
                    
                # Initialize missing fields
                if "settings" not in data:
                    data["settings"] = {
                        "referral_bonus": 0.5, "maintenance_mode": False,
                        "welcome_bonus": 2.0, "max_requests_per_day": 100,
                        "cooldown_period": 10
                    }
                if "stats" not in data:
                    data["stats"] = {
                        "total_requests": 0, "daily_requests": 0,
                        "successful_requests": 0, "failed_requests": 0,
                        "last_reset": datetime.now().isoformat(),
                        "peak_users": 0, "total_credits_distributed": 0
                    }
                if "analytics" not in data:
                    data["analytics"] = {
                        "popular_tools": {},
                        "error_logs": [],
                        "daily_stats": {}
                    }
                if "orders" not in data:
                    data["orders"] = {}
                if "query_history" not in data: # New field
                    data["query_history"] = []
                if "roles" not in data:
                    data["roles"] = {
                        "1": {"role_id": 1, "name": "Free User", "rate_limit": 100, "cooldown": 60, "grants_zc_per_day": 0},
                        "2": {"role_id": 2, "name": "Basic", "rate_limit": 200, "cooldown": 60, "grants_zc_per_day": 10},
                        "3": {"role_id": 3, "name": "Pro", "rate_limit": 500, "cooldown": 15, "grants_zc_per_day": 25},
                        "4": {"role_id": 4, "name": "Elite", "rate_limit": 1000, "cooldown": 3, "grants_zc_per_day": 50},
                        "5": {"role_id": 5, "name": "Admin", "rate_limit": 99999, "cooldown": 0, "grants_zc_per_day": 0}
                    }
                # Ensure new roles are added if upgrading from an older version
                if "2" not in data["roles"]:
                    data["roles"]["2"] = {"role_id": 2, "name": "Basic", "rate_limit": 200, "cooldown": 60, "grants_zc_per_day": 10}
                if "3" not in data["roles"]:
                    data["roles"]["3"] = {"role_id": 3, "name": "Pro", "rate_limit": 500, "cooldown": 15, "grants_zc_per_day": 25}
                if "4" not in data["roles"]:
                    data["roles"]["4"] = {"role_id": 4, "name": "Elite", "rate_limit": 1000, "cooldown": 3, "grants_zc_per_day": 50}
                if "5" not in data["roles"]:
                    data["roles"]["5"] = {"role_id": 5, "name": "Admin", "rate_limit": 99999, "cooldown": 0, "grants_zc_per_day": 0}
 
                if "version" not in data:
                    data["version"] = "2.3"
                    
                return data
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Database error: {e}")
                if os.path.exists(BACKUP_FILE):
                    try:
                        with open(BACKUP_FILE, "r") as f:
                            return json.load(f)
                    except:
                        pass
                DatabaseManager.initialize_db()
                return await DatabaseManager.load_db()

    @staticmethod
    async def save_db(data: Dict) -> bool:
        async with DatabaseManager._lock:
            try:
                # Create backup
                if os.path.exists(DATABASE_FILE):
                    if os.path.exists(BACKUP_FILE):
                        os.remove(BACKUP_FILE)
                    os.rename(DATABASE_FILE, BACKUP_FILE)
                
                with open(DATABASE_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                return True
            except Exception as e:
                logger.error(f"Failed to save database: {e}")
                # Restore backup if save failed
                if os.path.exists(BACKUP_FILE):
                    if os.path.exists(DATABASE_FILE):
                        os.remove(DATABASE_FILE)
                    os.rename(BACKUP_FILE, DATABASE_FILE)
                return False