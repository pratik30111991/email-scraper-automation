import time
import random
import re
import requests
import gspread
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheet Setup ---
SHEET_NAME = 'Sheet1'
LINK_COLUMN_HEADER = 'Links in group'
EMAIL_COLUMN = 'Email ID'
PHONE_COLUMN = 'Contact Number'
STATUS_COLUMN = 'Status'

# --- Authorize Google Sheets ---
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE')
worksheet = sheet.worksheet(SHEET_NAME)

# --- Helper functions ---
def extract_emails(text):
    return list(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)))

def extract_phones(text):
    return list(set(re.findall(r"(?:\+\d{1,3}\s?)?(?:\(\d{2,5}\)|\d{2,5})[\s.-]?\d{3,5}[\s.-]?\d{3,5}", text)))

def fetch_page_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.text
        return None
    except:
        return None

# --- Main Logic ---
rows = worksheet.get_all_records()
header = worksheet.row_values(1)

link_index = header.index(LINK_COLUMN_HEADER)
email_index = header.index(EMAIL_COLUMN)
phone_index = header.index(PHONE_COLUMN)
status_index = header.index(STATUS_COLUMN)

for i, row in enumerate(rows, start=2):  # Row 2 onwards
    url = row.get(LINK_COLUMN_HEADER)
    status = row.get(STATUS_COLUMN)

    if not url:
        worksheet.update_cell(i, status_index + 1, 'Skipped: No URL')
        continue
    if status in ['Done', 'Failed', 'Skipped: No URL']:
        continue

    html = fetch_page_content(url)
    if not html:
        worksheet.update_cell(i, status_index + 1, 'Failed')
        continue

    soup = BeautifulSoup(html, 'html.parser')
    emails = extract_emails(html)
    phones = extract_phones(html)

    email = emails[0] if emails else ''
    phone = phones[0] if phones else ''

    worksheet.update_cell(i, email_index + 1, email)
    worksheet.update_cell(i, phone_index + 1, phone)
    worksheet.update_cell(i, status_index + 1, 'Done' if email or phone else 'No data')

    time.sleep(random.uniform(5, 8))
