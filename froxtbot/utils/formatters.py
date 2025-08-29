import json
import asyncio
from typing import Dict, Optional, Tuple
from ..database.db_management import DatabaseManager
from ..config import DEFAULT_API_CONFIG
from .pagination import PaginationManager
from datetime import datetime

def format_response_for_telegram(response: Dict, tool_name: str, max_length: int = None) -> Tuple[str, Optional[Tuple[str, str]], dict]:
    """Format API response for Telegram message with pagination and file creation"""
    try:
        # Get max length from config
        if max_length is None:
            max_length = DEFAULT_API_CONFIG["MAX_PRETTY_PRINT_LENGTH"]
        
        # Clean sensitive data
        if isinstance(response, dict):
            filtered_response = {k: v for k, v in response.items() 
                               if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'key', 'secret'])}
        else:
            filtered_response = response
        
        # Create pretty JSON
        pretty_json = json.dumps(filtered_response, indent=2, ensure_ascii=False)
        
        # Check if response is large enough for pagination
        if len(pretty_json) > max_length:
            # Create paginated view
            paginated = PaginationManager.paginate_data(filtered_response, page=1, page_size=10)
            
            # Create summary for first page
            summary_json = json.dumps(paginated["page_data"], indent=2, ensure_ascii=False)
            
            # Create message with pagination info
            message_text = (
                f"```json\n{summary_json}\n```\n\n"
                f"📊 Results: {paginated['total_items']} items\n"
                f"📄 Showing page 1/{paginated['total_pages']}\n"
                f"📋 Full results available in attached file"
            )
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{tool_name}_result_{timestamp}.txt"
            
            # Create formatted content for file
            file_content = f"OSINT Tool: {tool_name.replace('_', ' ').title()}\n"
            file_content += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            file_content += f"{ '='*50}\n\n"
            file_content += f"Raw API Response:\n{pretty_json}"
            
            return message_text, (filename, file_content), paginated
        else:
            # Normal response
            code_block = f"```json\n{pretty_json}\n```"
            return code_block, None, {}
            
    except Exception as e:
        # logger.error(f"Error formatting response: {e}") # Logger not available here
        error_msg = f"```\nError formatting response: {str(e)}\nRaw response: {str(response)}\n```"
        return error_msg, None, {}