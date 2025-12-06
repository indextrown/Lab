import pandas as pd
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


GMAIL_ADDRESS = "indextrown@gmail.com"
TO_EMAIL = ["indextrown@gmail.com"]
GMAIL_APP_PASSWORD = "1234"

# ==========================
# 📬 메일 전송 함수
# ==========================
def send_gmail(subject, body):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD):
        print("✉️ Gmail 설정이 없어서 메일 전송 생략")
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = ", ".join(TO_EMAIL)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("❌ 메일 전송 실패:", e)

send_gmail("Test Subject", "This is a test email body.")