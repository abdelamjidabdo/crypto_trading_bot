import threading
import time
import os
# إنشاء مجلد logs تلقائيًا إن لم يكن موجودًا
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# إعداد التسجيل في ملف bot.log داخل مجلد logs
logging.basicConfig(
    filename=os.path.join(log_dir, 'bot.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
import logging

# استيرادات من باقي ملفات المشروع
from spot_monitor import start_spot_monitor
from utils import send_email
from config import (
    BITGET_API_KEY,
    BITGET_API_SECRET,
    BITGET_PASSPHRASE,
    GMAIL_USER,
    GMAIL_PASS,
    PURCHASE_AMOUNT
)
from bitget_client import BitgetClient

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
