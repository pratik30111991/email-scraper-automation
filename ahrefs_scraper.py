import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import re
import time
import phonenumbers

# === Google Sheet Setup ===
SHEET_ID = "1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ"
SHEET_NAME = "Sheet1"
REFERRING_URL_COL = 3  # C = 3
LINKS_IN_GROUP_COL = 33  # AG = 33
EMAIL_COL = 35  # AI
PHONE_COL = 36  # AJ
STATUS_COL = 37  # AK

# === Authenticate with Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)
worksheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# === Get all data ===
data = worksheet.get_all_values()

# === Email/Phone Regex ===
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def extract_emails_and_phones(html):
    emails = re.findall(EMAIL_REGEX, html)
    phones = []
    for match in phonenumbers.PhoneNumberMatcher(html, "IN"):
        phones.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
    return list(set(emails)), list(set(phones))

# === Loop through rows ===
for i, row in enumerate(data[1:], start=2):  # Start from row 2
    try:
        referring_url = row[REFERRING_URL_COL - 1]
        if not referring_url or "http" not in referring_url:
            continue

        email_cell = worksheet.cell(i, EMAIL_COL).value
        status_cell = worksheet.cell(i, STATUS_COL).value
        if email_cell or status_cell == "Done":
            continue  # Already processed

        print(f"[{i}] Scraping: {referring_url}")
        res = requests.get(referring_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        emails, phones = extract_emails_and_phones(text)
        email_str = ", ".join(emails)
        phone_str = ", ".join(phones)

        worksheet.update_cell(i, EMAIL_COL, email_str)
        worksheet.update_cell(i, PHONE_COL, phone_str)
        worksheet.update_cell(i, STATUS_COL, "Done")
        print(f"[{i}] ✅ Success: {email_str} | {phone_str}")
        time.sleep(10)

    except Exception as e:
        print(f"[{i}] ❌ Error: {str(e)}")
        worksheet.update_cell(i, STATUS_COL, "Error")
        time.sleep(5)
