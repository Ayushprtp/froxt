import math
from typing import Dict

class PaginationManager:
    @staticmethod
    def paginate_data(data: dict, page: int = 1, page_size: int = 10) -> dict:
        """Paginate dictionary data"""
        if not isinstance(data, dict):
            return {"page_data": data, "total_pages": 1, "current_page": 1}
        
        items = list(data.items()) if hasattr(data, 'items') else [(str(i), v) for i, v in enumerate(data)]
        total_items = len(items)
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_items = items[start_idx:end_idx]
        
        return {
            "page_data": dict(page_items),
            "total_pages": total_pages,
            "current_page": page,
            "total_items": total_items,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
