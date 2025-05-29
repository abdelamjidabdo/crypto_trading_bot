from config import GMAIL_USER, GMAIL_PASS
import smtplib
from email.mime.text import MIMEText
import logging

logging.basicConfig(filename='logs/bot.log', level=logging.INFO)

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        logging.info(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Email send failed: {e}")
