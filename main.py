import re
import time
import requests
import gspread
from bs4 import BeautifulSoup
from random import randint
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Sheet config
sheet = client.open_by_key("1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ")
worksheet = sheet.worksheet("Sheet1")

# Column positions
URL_COL = worksheet.row_values(1).index("Links in group") + 1
EMAIL_COL = URL_COL + 2
PHONE_COL = URL_COL + 3
STATUS_COL = URL_COL + 4

# Get all rows
all_rows = worksheet.get_all_values()

# Process each row
for i, row in enumerate(all_rows[1:], start=2):  # Skip header row
    try:
        url = row[URL_COL - 1]
        status = row[STATUS_COL - 1] if len(row) >= STATUS_COL else ""

        if not url.strip() or status in ["Done", "Failed", "Skipped"]:
            continue

        print(f"Scraping row {i}: {url}")
        time.sleep(randint(5, 8))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/102.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=20)

        if not r.ok:
            worksheet.update_cell(i, STATUS_COL, "Failed")
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()

        emails = set(re.findall(r"[\w\.-]+@[\w\.-]+", text))
        phones = set(re.findall(r"(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3}[-.\s]?\d{4,6}", text))

        email_val = ", ".join(emails) if emails else "Not Found"
        phone_val = ", ".join(phones) if phones else "Not Found"

        worksheet.update_cell(i, EMAIL_COL, email_val)
        worksheet.update_cell(i, PHONE_COL, phone_val)
        worksheet.update_cell(i, STATUS_COL, "Done")

    except Exception as e:
        print(f"Row {i} error: {e}")
        worksheet.update_cell(i, STATUS_COL, "Failed")
