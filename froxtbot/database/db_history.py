import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from .db_management import DatabaseManager

logger = logging.getLogger(__name__)

async def log_query_history(user_id: int, service_name: str, query_text: str) -> bool:
    """Logs a specific service query to the query_history in the database."""
    try:
        db = await DatabaseManager.load_db()
        db.setdefault("query_history", []).append({
            "user_id": user_id,
            "service_name": service_name,
            "query_text": query_text,
            "timestamp": datetime.now().isoformat()
        })
        # Keep history to a reasonable size (e.g., last 1000 queries)
        db["query_history"] = db["query_history"][-1000:]
        await DatabaseManager.save_db(db)
        logger.info(f"Logged query for user {user_id} on service {service_name}.")
        return True
    except Exception as e:
        logger.error(f"Error logging query history for user {user_id}, service {service_name}: {e}")
        return False

async def get_user_query_history(
    user_id: int,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "timestamp",
    service_name: Optional[str] = None,
    time_period: Optional[str] = None,
) -> Tuple[List[Dict], int]:
    """Fetches a paginated and sorted list of a specific user's query history."""
    try:
        db = await DatabaseManager.load_db()
        all_history = [entry for entry in db.get("query_history", []) if entry["user_id"] == user_id]

        if service_name:
            all_history = [entry for entry in all_history if entry["service_name"].lower() == service_name.lower()]

        if time_period:
            now = datetime.now()
            filtered_history = []
            for entry in all_history:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if time_period == "today" and (now - entry_time).days < 1:
                    filtered_history.append(entry)
                elif time_period == "yesterday" and (now - entry_time).days >= 1 and (now - entry_time).days < 2:
                    filtered_history.append(entry)
                elif time_period == "week" and (now - entry_time).days < 7:
                    filtered_history.append(entry)
            all_history = filtered_history

        # Sort
        all_history.sort(key=lambda x: datetime.fromisoformat(x.get(sort_by, datetime.min.isoformat())), reverse=True)

        # Paginate
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_history = all_history[start_index:end_index]
        
        return paginated_history, len(all_history)
    except Exception as e:
        logger.error(f"Error getting user query history for user {user_id}: {e}")
        return [], 0

async def get_all_query_history(
    page: int = 1,
    limit: int = 10,
    sort_by: str = "timestamp",
    service_name: Optional[str] = None,
    user_id: Optional[int] = None,
    time_period: Optional[str] = None,
) -> Tuple[List[Dict], int]:
    """Fetches a paginated and sorted list of all query history (for admin)."""
    try:
        db = await DatabaseManager.load_db()
        all_history = list(db.get("query_history", []))

        if service_name:
            all_history = [entry for entry in all_history if entry["service_name"].lower() == service_name.lower()]
        
        if user_id:
            all_history = [entry for entry in all_history if entry["user_id"] == user_id]

        if time_period:
            now = datetime.now()
            filtered_history = []
            for entry in all_history:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if time_period == "today" and (now - entry_time).days < 1:
                    filtered_history.append(entry)
                elif time_period == "yesterday" and (now - entry_time).days >= 1 and (now - entry_time).days < 2:
                    filtered_history.append(entry)
                elif time_period == "week" and (now - entry_time).days < 7:
                    filtered_history.append(entry)
            all_history = filtered_history

        # Sort
        all_history.sort(key=lambda x: datetime.fromisoformat(x.get(sort_by, datetime.min.isoformat())), reverse=True)

        # Paginate
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_history = all_history[start_index:end_index]
        
        return paginated_history, len(all_history)
    except Exception as e:
        logger.error(f"Error getting all query history: {e}")
        return [], 0
