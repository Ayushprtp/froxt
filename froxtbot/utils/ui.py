from ..config import logger

class UIElements:
    EMOJIS = {
        "search": "🔍", "credits": "💎", "user": "👤", "admin": "👑",
        "tools": "🛠️", "back": "🔙", "home": "🏠", "info": "ℹ️",
        "warning": "⚠️", "success": "✅", "error": "❌", "lock": "🔒",
        "unlock": "🔓", "stats": "📊", "settings": "⚙️", "referral": "🎁",
        "buy": "💳", "support": "📞", "document": "📄", "mobile": "📱",
        "email": "📧", "aadhar": "🆔", "upi": "💰", "password": "🔑",
        "ip": "🌐", "bike": "🏍️", "car": "🚗", "voter": "🗳️",
        "ration": "🍞", "vehicle": "🚙", "breach": "🔓", "deep": "🔬",
    }

    BUTTON_STYLES = {
        "primary": "🔹 ",
        "secondary": "▫️ ",
        "premium": "💎 ",
        "free": "🆓 ",
        "danger": "🔥 ",
        "success": "✅ ",
        "info": "ℹ️ ",
        "warning": "⚠️ ",
    }

    @staticmethod
    def format_number(num):
        return f"{num:,}"
