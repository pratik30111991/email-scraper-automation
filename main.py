import os
import json
import base64
import smtplib
import imaplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pytz import timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === SETTINGS ===
TIMEZONE = 'Asia/Kolkata'
SHEET_ID = os.getenv('SHEET_ID')
TRACKING_BACKEND = "https://auto-email-scheduler.onrender.com"

# === AUTHENTICATE GOOGLE SHEETS ===
creds_json = json.loads(os.getenv('GOOGLE_JSON'))
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(credentials)

# === LOAD SHEET ===
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet("Sales_Mails")

# === READ ALL ROWS ===
rows = worksheet.get_all_records()
now = datetime.now(timezone(TIMEZONE))

for idx, row in enumerate(rows, start=2):  # start=2 because of header row
    try:
        email_id = row.get('Email ID', '').strip()
        name = row.get('Name', '').strip()
        subject = row.get('Subject', '').strip()
        message = row.get('Message', '').strip()
        schedule_str = row.get('Schedule Date & Time', '').strip()
        status = row.get('Status', '').strip()

        if not email_id or not name or not schedule_str or status:
            continue

        try:
            schedule_time = datetime.strptime(schedule_str, "%d/%m/%Y %H:%M:%S").astimezone(timezone(TIMEZONE))
        except ValueError:
            worksheet.update_acell(f'H{idx}', "Skipped: Invalid Date Format")
            continue

        if now < schedule_time:
            continue

        # Add tracking pixel
        tracking_url = f"{TRACKING_BACKEND}/track?sheet=Sales_Mails&row={idx}&email={email_id}"
        full_message = f'{message}<br><img src="{tracking_url}" width="1" height="1">'

        # Send Email
        from_email = os.getenv("SMTP_EMAIL")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        smtp_host = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        msg = MIMEMultipart()
        msg['To'] = email_id
        msg['From'] = f"Unlisted Radar <{from_email}>"
        msg['Subject'] = subject
        msg['Date'] = email.utils.format_datetime(now)
        msg.attach(MIMEText(full_message, 'html'))

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(from_email, smtp_pass)
        server.sendmail(from_email, email_id, msg.as_string())
        server.quit()

        # Mark status
        worksheet.update(f'H{idx}', 'Sent')
        worksheet.update(f'I{idx}', now.strftime('%d/%m/%Y %H:%M:%S'))

    except Exception as e:
        worksheet.update(f'H{idx}', f'Failed: {str(e)}')
