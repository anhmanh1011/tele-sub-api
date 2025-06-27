import logging
import json
import requests

# Cấu hình logging cho API
api_logger = logging.getLogger("api_logger")
api_handler = logging.FileHandler("api.log", encoding="utf-8")
api_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not api_logger.hasHandlers():
    api_logger.addHandler(api_handler)
api_logger.setLevel(logging.INFO)

with open("config.json", "r") as f:
    config = json.load(f)

SNUSBASE_API_KEY = config["SNUSBASE_API_KEY"]
SNUSBASE_API_URL = "https://api.snusbase.com/data/search"

def search_domains(domains):
    headers = {
        "Auth": SNUSBASE_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "terms": domains,
        "types": ["_domain"]
    }
    try:
        api_logger.info(f"Request: {data}")
        response = requests.post(SNUSBASE_API_URL, headers=headers, json=data)
        api_logger.info(f"Response: {response.status_code} {response.text[:500]}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        api_logger.error(f"API call failed: {str(e)}")
        raise 