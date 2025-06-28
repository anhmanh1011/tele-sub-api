import logging
import json
import requests
import time

# Cấu hình logging cho API
api_logger = logging.getLogger("api_logger")
api_handler = logging.FileHandler("api.log", encoding="utf-8")
api_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not api_logger.hasHandlers():
    api_logger.addHandler(api_handler)
api_logger.setLevel(logging.INFO)

with open("config.json", "r") as f:
    config = json.load(f)

# Hỗ trợ nhiều API key
SNUSBASE_API_KEYS = config.get("SNUSBASE_API_KEYS", [config.get("SNUSBASE_API_KEY", "")])
if isinstance(SNUSBASE_API_KEYS, str):
    SNUSBASE_API_KEYS = [SNUSBASE_API_KEYS]

SNUSBASE_API_URL = "https://api.snusbase.com/data/search"

def search_domains(domains, max_retries=3):
    """
    Tìm kiếm domains với khả năng tự động chuyển key khi gặp lỗi
    """
    for attempt in range(max_retries):
        for key_index, api_key in enumerate(SNUSBASE_API_KEYS):
            if not api_key.strip():
                continue
                
            headers = {
                "Auth": api_key,
                "Content-Type": "application/json"
            }
            data = {
                "terms": domains,
                "types": ["_domain"]
            }
            
            try:
                api_logger.info(f"Thử với key {key_index + 1}/{len(SNUSBASE_API_KEYS)} (lần thử {attempt + 1}/{max_retries})")
                response = requests.post(SNUSBASE_API_URL, headers=headers, json=data, timeout=30)
                
                if response.status_code == 200:
                    api_logger.info(f"Thành công với key {key_index + 1}")
                    return response.json()
                elif response.status_code == 401:
                    api_logger.warning(f"Key {key_index + 1} không hợp lệ (401), thử key tiếp theo")
                    continue
                elif response.status_code == 429:
                    api_logger.warning(f"Key {key_index + 1} bị rate limit (429), thử key tiếp theo")
                    continue
                else:
                    api_logger.error(f"Lỗi HTTP {response.status_code} với key {key_index + 1}: {response.text[:200]}")
                    response.raise_for_status()
                    
            except requests.exceptions.Timeout:
                api_logger.warning(f"Timeout với key {key_index + 1}, thử key tiếp theo")
                continue
            except requests.exceptions.RequestException as e:
                api_logger.error(f"Lỗi request với key {key_index + 1}: {str(e)}")
                continue
            except Exception as e:
                api_logger.error(f"Lỗi không xác định với key {key_index + 1}: {str(e)}")
                continue
        
        # Nếu đã thử hết tất cả key mà vẫn lỗi, chờ một chút rồi thử lại
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 5  # Tăng thời gian chờ theo số lần thử
            api_logger.info(f"Đã thử hết tất cả key, chờ {wait_time} giây trước khi thử lại")
            time.sleep(wait_time)
    
    # Nếu đã thử hết tất cả key và lần thử mà vẫn lỗi
    api_logger.error("Đã thử hết tất cả key và lần thử mà vẫn không thành công")
    raise Exception("Không thể kết nối với Snusbase API sau khi thử tất cả key") 