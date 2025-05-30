import time
import json
import os
import logging
from datetime import datetime
from bitget_client import BitgetClient
from utils import send_email
from config import PURCHASE_AMOUNT

os.makedirs("logs", exist_ok=True)

SEEN_FILE = "logs/seen.json"
client = BitgetClient()

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Error reading seen.json: {e}")
            return {}
    return {}

def save_seen(data):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving seen.json: {e}")

def start_spot_monitor():
    seen = load_seen()

    # ✅ تجاهل العملات الحالية عند أول تشغيل
    if not seen:
        print("[Monitor] First run detected, initializing seen.json...")
        try:
            symbols = client.get_symbols()
            seen = {
                sym: {"status": "ignored", "time": datetime.utcnow().isoformat()}
                for sym in symbols if sym.endswith("USDT")
            }
            save_seen(seen)
            print("[Monitor] Initial seen.json created with existing symbols.")
        except Exception as e:
            send_email("Bot Error", f"Failed to initialize seen.json: {str(e)}")
            return

    while True:
        try:
            symbols = client.get_symbols()
            new = [s for s in symbols if s not in seen and s.endswith("USDT")]
            for sym in new:
                timestamp = datetime.utcnow().isoformat()
                send_email(f"New Coin Detected: {sym}", f"New listing on Bitget: {sym} at {timestamp}")
                success = client.place_market_order(sym, PURCHASE_AMOUNT)
                if success:
                    send_email(f"Purchase Success: {sym}", f"Successfully bought {sym} at {timestamp}")
                    seen[sym] = {"status": "bought", "time": timestamp}
                else:
                    send_email(f"Purchase Failed: {sym}", f"Failed to buy {sym} after retries.")
                    seen[sym] = {"status": "failed", "time": timestamp}
            save_seen(seen)
        except Exception as e:
            logging.error(f"Error in monitoring loop: {str(e)}")
            send_email("Bot Error", f"Error in monitoring loop: {str(e)}")
        time.sleep(0.7)
