import re
import time
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(credentials)

# Open sheet
sheet_url = 'https://docs.google.com/spreadsheets/d/1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ/edit'
doc = gc.open_by_url(sheet_url)
sheet = doc.worksheet('Sheet1')

# Column positions
URL_COL = 3      # Referring page URL
STATUS_COL = 39  # AM
EMAIL_COL = 37   # AK
PHONE_COL = 38   # AL

# Clean email function
def is_valid_email(email):
    if any(ext in email.lower() for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp', '.js', '.css', '.ico']):
        return False
    return '@' in email and '.' in email.split('@')[-1]

# Clean phone function
def clean_phone(phone):
    phone = re.sub(r'[^\d+]', '', phone)  # remove everything except digits and +
    return phone if 7 <= len(phone) <= 15 else ''

# Extract contacts
def extract_contacts(html):
    emails_raw = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))
    phones_raw = list(set(re.findall(r"\+?\d[\d\s\-().]{7,}\d", html)))

    emails = [e for e in emails_raw if is_valid_email(e)]
    phones = [clean_phone(p) for p in phones_raw if clean_phone(p)]

    return emails, phones

# URL validator
def is_valid_domain(url):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https']

def main():
    rows = sheet.get_all_values()

    for idx, row in enumerate(rows[1:], start=2):  # skip header
        url = row[URL_COL - 1].strip()
        status = row[STATUS_COL - 1].strip() if len(row) >= STATUS_COL else ''

        if status.lower() == 'done' or not url:
            continue

        if not is_valid_domain(url):
            sheet.update_cell(idx, STATUS_COL, 'Invalid URL')
            continue

        print(f"[{idx}] Scraping: {url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            html = resp.text

            emails, phones = extract_contacts(html)

            sheet.update_cell(idx, EMAIL_COL, emails[0] if emails else '')
            sheet.update_cell(idx, PHONE_COL, phones[0] if phones else '')
            sheet.update_cell(idx, STATUS_COL, 'Done')

        except Exception as e:
            sheet.update_cell(idx, STATUS_COL, f"Error: {str(e)}")
            print(f"[ERROR row {idx}] {e}")

        time.sleep(5)  # avoid rate-limit or IP ban

if __name__ == '__main__':
    main()
