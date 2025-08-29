import asyncio
import aiohttp
import json
from typing import Dict, Optional, Union, Tuple
from ..database.db_management import DatabaseManager
from ..config import SERVICES_CONFIG, DEFAULT_API_CONFIG, logger

class APIManager:
    @staticmethod
    async def make_request(url: str, method: str = "GET", data: dict = None, headers: dict = None) -> dict:
        timeout_val = DEFAULT_API_CONFIG["REQUEST_TIMEOUT"]
        max_retries = DEFAULT_API_CONFIG["MAX_RETRIES"]
        retry_delay = DEFAULT_API_CONFIG["RETRY_DELAY"]
        
        headers = headers or {"Connection": "close", "User-Agent": "Mozilla/5.0"}
        
        connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300, use_dns_cache=True)
        timeout = aiohttp.ClientTimeout(total=timeout_val)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for attempt in range(max_retries):
                try:
                    if method.upper() == "GET":
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                try:
                                    return await response.json()
                                except:
                                    text_response = await response.text()
                                    return {"raw_response": text_response, "status": response.status}
                            else:
                                return {"error": f"HTTP {response.status}", "message": await response.text()}
                    else:
                        async with session.post(url, json=data, headers=headers) as response:
                            if response.status == 200:
                                try:
                                    return await response.json()
                                except:
                                    text_response = await response.text()
                                    return {"raw_response": text_response, "status": response.status}
                            else:
                                return {"error": f"HTTP {response.status}", "message": await response.text()}
                                
                except aiohttp.ClientConnectorError as e:
                    logger.error(f"Connection error for {url}: {e}")
                    if attempt == max_retries - 1:
                        return {"error": "Connection failed", "message": str(e), "attempt": attempt + 1}
                    await asyncio.sleep(retry_delay)
                except aiohttp.ClientTimeoutError as e:
                    logger.warning(f"Request timeout for {url}, attempt {attempt + 1}/{max_retries}")
                    if attempt == max_retries - 1:
                        return {"error": "Request timeout", "message": str(e), "attempt": attempt + 1}
                    await asyncio.sleep(retry_delay)
                except aiohttp.ClientResponseError as e:
                    logger.error(f"HTTP error for {url}: {e.status} - {e.message}")
                    return {"error": f"HTTP {e.status}", "message": e.message}
                except aiohttp.ClientError as e:
                    logger.error(f"Client error for {url}: {e}")
                    if attempt == max_retries - 1:
                        return {"error": "API request failed", "message": str(e), "attempt": attempt + 1}
                    await asyncio.sleep(retry_delay)
                except asyncio.TimeoutError as e:
                    logger.warning(f"Async timeout for {url}, attempt {attempt + 1}/{max_retries}")
                    if attempt == max_retries - 1:
                        return {"error": "Request timeout", "message": str(e), "attempt": attempt + 1}
                    await asyncio.sleep(retry_delay)
                except Exception as e:
                    logger.error(f"Unexpected error for {url}: {e}")
                    if attempt == max_retries - 1:
                        return {"error": "Unexpected error", "message": str(e), "attempt": attempt + 1}
                    await asyncio.sleep(retry_delay)
        
        return {"error": "Max retries reached"}

async def execute_tool_request(tool: str, input_data: str) -> dict:
    """Execute API request for the specified tool"""
    try:
        # Get service details from the SERVICES configuration
        services = SERVICES_CONFIG
        
        if tool not in services:
            return {"error": "Unknown tool", "message": f"Tool '{tool}' is not supported"}
            
        service_info = services[tool]
        url = service_info["serviceapi"]
        
        # Check if service is enabled
        if not service_info.get("enabled", True):
            return {"error": "Service disabled", "message": f"Tool '{tool}' is currently disabled"}
        
        # Handle different request types
        if tool in ["mobile", "email", "aadhar", "num2upi", "bike_info", "voterid", "car_lookup", "fam_pay", "upi_info", "ration_card", "vehicle_info", "breach_check", "deep_scan"]:
            # GET requests with query parameter
            full_url = f"{url}{input_data}"
            logger.info(f"Making {tool} request for: {input_data}")
            return await APIManager.make_request(full_url)
        elif tool in ["username_scan", "email_scan", "password_analyze", "ip_scan", "full_scan"]:
            # POST requests with JSON data
            logger.info(f"Making {tool} request for: {input_data}")
            return await APIManager.make_request(
                url,
                method="POST",
                data={tool.split('_')[0]: input_data}  # username, email, password, ip, full
            )
        elif tool == "upi_verify":
            logger.info(f"Making UPI verify request for: {input_data}")
            return await APIManager.make_request(
                url,
                method="POST",
                data={'vpa': input_data, 'merchant_id': 'paytm'},
                headers={'Content-Type': 'application/json', 'Connection': 'close'}
            )
        else:
            return {"error": "Unknown tool", "message": f"Tool '{tool}' is not supported"}
    except Exception as e:
        logger.error(f"Error in execute_tool_request: {e}")
        return {"error": "Execution failed", "message": str(e)}
