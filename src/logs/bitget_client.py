import time
import hashlib
import hmac
import base64
import requests
import json
import logging
import os
from config import BITGET_API_KEY, BITGET_API_SECRET, BITGET_PASSPHRASE
from utils import send_email
from datetime import datetime, timedelta

BASE_URL = "https://api.bitget.com"

# Constants specific to place_market_order only
ORDER_MAX_RETRIES = 5
ORDER_TIMEOUT = 1

RATE_LIMIT_LOG = "logs/rate_limit_429.log"

def log_rate_limit():
    now = datetime.utcnow().isoformat()
    with open(RATE_LIMIT_LOG, "a") as f:
        f.write(now + "\n")

def count_recent_rate_limits(minutes=60):
    if not os.path.exists(RATE_LIMIT_LOG):
        return 0
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    with open(RATE_LIMIT_LOG) as f:
        timestamps = [line.strip() for line in f.readlines()]
    times = [datetime.fromisoformat(t) for t in timestamps if t]
    return sum(1 for t in times if t > cutoff)

class BitgetClient:
    def __init__(self):
        self.session = requests.Session()

    def _get_headers(self, method, endpoint, body=""):
        timestamp = str(int(time.time() * 1000))
        pre_hash = timestamp + method.upper() + endpoint + body
        sign = hmac.new(BITGET_API_SECRET.encode(), pre_hash.encode(), hashlib.sha256).digest()
        sign_b64 = base64.b64encode(sign).decode()
        return {
            "ACCESS-KEY": BITGET_API_KEY,
            "ACCESS-SIGN": sign_b64,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": BITGET_PASSPHRASE,
            "Content-Type": "application/json"
        }

    def get_symbols(self):
        endpoint = "/api/spot/v1/public/symbols"
        url = BASE_URL + endpoint
        for attempt in range(5):  # Local retry count for get_symbols only
            try:
                res = self.session.get(url, timeout=2)  # Local timeout for get_symbols
                if res.status_code == 200:
                    json_data = res.json()
                    data = json_data.get("data", [])
                    return [item["symbolName"] for item in data if item.get("status") == "online"]
                elif res.status_code == 429:
                    log_rate_limit()
                    recent_429s = count_recent_rate_limits()
                    logging.warning(f"Rate limited (429) on get_symbols. Recent 429s in last hour: {recent_429s}")
                    if recent_429s > 3:
                        send_email("Bot Warning: Frequent 429 errors",
                                   f"More than 3 rate limit (429) errors occurred in the past hour.")
                    wait_time = 10 + attempt * 5
                    time.sleep(wait_time)
                else:
                    logging.warning(f"get_symbols attempt {attempt}: Status {res.status_code}")
                time.sleep(1)  # Ensure 1-second delay between all attempts
            except Exception as e:
                logging.error(f"get_symbols exception: {e}")
                time.sleep(1)
        return []

    def place_market_order(self, symbol, size):
        endpoint = "/api/spot/v1/trade/orders"
        url = BASE_URL + endpoint
        body = json.dumps({
            "symbol": symbol,
            "side": "buy",
            "orderType": "market",
            "force": "gtc",
            "size": str(size)
        })
        headers = self._get_headers("POST", endpoint, body)
        for attempt in range(ORDER_MAX_RETRIES):
            try:
                res = self.session.post(url, headers=headers, data=body, timeout=ORDER_TIMEOUT)
                if res.status_code == 200:
                    result = res.json()
                    if result.get("code") == "00000":
                        return True
                    else:
                        logging.warning(f"place_market_order failed: {result}")
                else:
                    logging.warning(f"place_market_order HTTP {res.status_code}: {res.text}")
                time.sleep(1)  # Wait between attempts
            except Exception as e:
                logging.error(f"place_market_order exception: {e}")
                time.sleep(1)
        return False
