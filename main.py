import os

# ✨ أولاً: تأكد من وجود مجلد logs
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)  # ← أكثر أمانًا من if

import threading
import time
import logging
from spot_monitor import start_spot_monitor

# إعداد التسجيل في ملف bot.log داخل مجلد logs
logging.basicConfig(
    filename=os.path.join(log_dir, 'bot.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_event(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[Main] {timestamp} | {msg}")
    logging.info(msg)

def run_monitor():
    while True:
        try:
            log_event("Starting spot monitor thread...")
            start_spot_monitor()
        except Exception as e:
            log_event(f"Error in spot monitor: {e}. Restarting in 5 seconds...")
            time.sleep(5)

def start_bot():
    log_event("Starting bot...")
    thread = threading.Thread(target=run_monitor, name="SpotMonitor")
    thread.daemon = True
    thread.start()
    while True:
        time.sleep(5)

if __name__ == "__main__":
    start_bot()
