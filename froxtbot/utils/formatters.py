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
        
        # Convert to plain text with enhanced styling
        plain_text = convert_json_to_styled_text(filtered_response, tool_name)
        
        # Check if response is large enough for pagination
        if len(plain_text) > max_length:
            # Create paginated view
            paginated = PaginationManager.paginate_data(filtered_response, page=1, page_size=10)
            
            # Create summary for first page
            summary_text = convert_json_to_styled_text(paginated["page_data"], tool_name)
            
            # Create message with pagination info
            message_text = (
                f"{summary_text}\n\n"
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
            file_content += f"{'='*50}\n\n"
            file_content += f"Raw API Response:\n{pretty_json}"
            
            return message_text, (filename, file_content), paginated
        else:
            # Normal response
            return plain_text, None, {}
            
    except Exception as e:
        # logger.error(f"Error formatting response: {e}") # Logger not available here
        error_msg = f"Error formatting response: {str(e)}\nRaw response: {str(response)}"
        return error_msg, None, {}

def convert_json_to_styled_text(data, tool_name: str) -> str:
    """Convert JSON data to styled plain text for Telegram"""
    try:
        # Add header with timestamp and tool info
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"🔍 OSINT Tool Results\n"
            f"🛠️ Tool: {tool_name.replace('_', ' ').title()}\n"
            f"🕐 Timestamp: {timestamp}\n"
            f"{'─'*30}\n\n"
        )
        
        # Convert data to styled text
        if isinstance(data, dict):
            styled_text = format_dict(data, 0)
        elif isinstance(data, list):
            styled_text = format_list(data, 0)
        else:
            styled_text = str(data)
        
        return f"{header}{styled_text}"
    except Exception as e:
        return f"Error converting data: {str(e)}\nRaw data: {str(data)}"

def format_dict(d: dict, indent_level: int) -> str:
    """Format dictionary as styled text"""
    lines = []
    indent = "  " * indent_level
    
    for key, value in d.items():
        if isinstance(value, dict):
            lines.append(f"{indent}🔹 {key}:")
            lines.append(format_dict(value, indent_level + 1))
        elif isinstance(value, list):
            lines.append(f"{indent}🔹 {key}:")
            lines.append(format_list(value, indent_level + 1))
        else:
            lines.append(f"{indent}🔸 {key}: {value}")
    
    return "\n".join(lines)

def format_list(l: list, indent_level: int) -> str:
    """Format list as styled text"""
    lines = []
    indent = "  " * indent_level
    
    for i, item in enumerate(l):
        if isinstance(item, dict):
            lines.append(f"{indent}🔸 Item {i+1}:")
            lines.append(format_dict(item, indent_level + 1))
        elif isinstance(item, list):
            lines.append(f"{indent}🔸 Item {i+1}:")
            lines.append(format_list(item, indent_level + 1))
        else:
            lines.append(f"{indent}🔸 {item}")
    
    return "\n".join(lines)