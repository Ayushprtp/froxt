import json
from typing import Dict, Any

# Services Configuration
# This configuration is used to define all available OSINT tools in the bot
# Each service has the following properties:
# - servicename: The internal name of the service
# - servicecost: The cost in credits to use the service (0 for free)
# - servicebeautify: The display name with emoji for the service
# - serviceapi: The API endpoint for the service
# - cmdalias: The command alias for the service
# - input_prompt: The prompt to show when asking for input
# - enabled: Whether the service is enabled or disabled

SERVICES_CONFIG: Dict[str, Dict[str, Any]] = {
    "mobile": {
        "servicename": "Mobile Lookup",
        "servicecost": 0,
        "servicebeautify": "📱 Mobile Lookup",
        "serviceapi": "https://numinfoapi.zerovault.workers.dev/search/mobile?value=",
        "cmdalias": "mobile",
        "input_prompt": "📱 Enter mobile number (with or without country code)",
        "enabled": True
    },
    "email": {
        "servicename": "Email Lookup",
        "servicecost": 0,
        "servicebeautify": "📧 Email Lookup",
        "serviceapi": "https://numinfoapi.zerovault.workers.dev/search/email?value=",
        "cmdalias": "email",
        "input_prompt": "📧 Enter email address",
        "enabled": True
    },
    "aadhar": {
        "servicename": "Aadhar Search",
        "servicecost": 0,
        "servicebeautify": "🆔 Aadhar Search",
        "serviceapi": "https://numinfoapi.zerovault.workers.dev/search/aadhaar?value=",
        "cmdalias": "aadhar",
        "input_prompt": "🆔 Enter Aadhar number",
        "enabled": True
    },
    "num2upi": {
        "servicename": "Num2UPI",
        "servicecost": 0,
        "servicebeautify": "💰 Num2UPI",
        "serviceapi": "https://num2upi.zerovault.workers.dev/?number=",
        "cmdalias": "num2upi",
        "input_prompt": "📱 Enter mobile number",
        "enabled": True
    },
    "username_scan": {
        "servicename": "Username Scan",
        "servicecost": 0,
        "servicebeautify": "👤 Username Scan",
        "serviceapi": "https://osintapi.zerovault.workers.dev/api/scan/username",
        "cmdalias": "username",
        "input_prompt": "👤 Enter username to scan",
        "enabled": True
    },
    "email_scan": {
        "servicename": "Email Scan",
        "servicecost": 0,
        "servicebeautify": "📧 Email Scan",
        "serviceapi": "https://osintapi.zerovault.workers.dev/api/scan/email",
        "cmdalias": "emailscan",
        "input_prompt": "📧 Enter email to scan",
        "enabled": True
    },
    "password_analyze": {
        "servicename": "Password Analyze",
        "servicecost": 0,
        "servicebeautify": "🔑 Password Analyze",
        "serviceapi": "https://osintapi.zerovault.workers.dev/api/scan/password",
        "cmdalias": "password",
        "input_prompt": "🔑 Enter password to analyze",
        "enabled": True
    },
    "ip_scan": {
        "servicename": "IP Scanner",
        "servicecost": 0,
        "servicebeautify": "🌐 IP Scanner",
        "serviceapi": "https://osintapi.zerovault.workers.dev/api/scan/ip",
        "cmdalias": "ip",
        "input_prompt": "🌐 Enter IP address",
        "enabled": True
    },
    "full_scan": {
        "servicename": "Full Scan",
        "servicecost": 0,
        "servicebeautify": "🔍 Full Scan",
        "serviceapi": "https://osintapi.zerovault.workers.dev/api/scan/full",
        "cmdalias": "fullscan",
        "input_prompt": "🔍 Enter target for full scan",
        "enabled": True
    },
    "bike_info": {
        "servicename": "Bike Info",
        "servicecost": 0,
        "servicebeautify": "🏍️ Bike Info",
        "serviceapi": "http://46.202.163.144:2050/vehicle?bike=",
        "cmdalias": "bike",
        "input_prompt": "🏍️ Enter bike registration number",
        "enabled": True
    },
    "voterid": {
        "servicename": "Voter ID",
        "servicecost": 0,
        "servicebeautify": "🗳️ Voter ID",
        "serviceapi": "http://46.202.163.144:2051/voterid?info=",
        "cmdalias": "voterid",
        "input_prompt": "🗳️ Enter voter ID",
        "enabled": True
    },
    "car_lookup": {
        "servicename": "Vehicle Lookup",
        "servicecost": 0,
        "servicebeautify": "🚗 Vehicle Lookup",
        "serviceapi": "https://cars-consumer.cars24.team/api/v1/product/service-history?regNumber=",
        "cmdalias": "car",
        "input_prompt": "🚗 Enter car registration number",
        "enabled": True
    },
    "fam_pay": {
        "servicename": "FamPay Info",
        "servicecost": 0,
        "servicebeautify": "💳 FamPay Info",
        "serviceapi": "http://46.202.163.144:2055/fam?info=",
        "cmdalias": "fampay",
        "input_prompt": "💳 Enter FamPay info",
        "enabled": True
    },
    "upi_info": {
        "servicename": "UPI Info",
        "servicecost": 0,
        "servicebeautify": "💰 UPI Info",
        "serviceapi": "http://46.202.163.144:2056/upi?info=",
        "cmdalias": "upiinfo",
        "input_prompt": "💰 Enter UPI ID",
        "enabled": True
    },
    "upi_verify": {
        "servicename": "UPI Verify",
        "servicecost": 0,
        "servicebeautify": "✅ UPI Verify",
        "serviceapi": "https://api.juspay.in/upi/verify-vpa",
        "cmdalias": "upiverify",
        "input_prompt": "✅ Enter UPI ID to verify",
        "enabled": True
    },
    "ration_card": {
        "servicename": "Ration Card",
        "servicecost": 0,
        "servicebeautify": "🍞 Ration Card",
        "serviceapi": "https://impds.nic.in/sale/RationCardDetailsfetch?fpsrcardno=",
        "cmdalias": "rationcard",
        "input_prompt": "🍞 Enter ration card number",
        "enabled": True
    },
    "vehicle_info": {
        "servicename": "Vehicle Info",
        "servicecost": 0,
        "servicebeautify": "🚙 Vehicle Info",
        "serviceapi": "https://vehicleinfo.zerovault.workers.dev/?VIN=",
        "cmdalias": "vehicle",
        "input_prompt": "🚙 Enter vehicle VIN number",
        "enabled": True
    },
    "breach_check": {
        "servicename": "Breach Check",
        "servicecost": 0,
        "servicebeautify": "🔓 Breach Check",
        "serviceapi": "https://breachchk.zerovault.workers.dev/query?value=",
        "cmdalias": "breach",
        "input_prompt": "🔓 Enter email, username, IP, phone or domain to check for breaches",
        "enabled": True
    },
    "deep_scan": {
        "servicename": "Deep Scan",
        "servicecost": 5,
        "servicebeautify": "🔬 Deep Scan",
        "serviceapi": "https://haxorrand.thelolipol.workers.dev/deep_search?mobile=",
        "cmdalias": "deepscan",
        "input_prompt": "🔬 Enter mobile number for deep analysis (comprehensive data)",
        "enabled": True
    }
}
