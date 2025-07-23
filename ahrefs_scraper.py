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

sheet_url = 'https://docs.google.com/spreadsheets/d/1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ/edit'
doc = gc.open_by_url(sheet_url)
sheet = doc.worksheet('Sheet1')

# Column definitions
URL_COL = 3      # Referring page URL
STATUS_COL = 39  # AM = Status
EMAIL_COL = 37   # AK
PHONE_COL = 38   # AL

def extract_contacts(html):
    emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))
    phones = list(set(re.findall(r"\+?\d[\d\s\-().]{7,}\d", html)))
    return emails, phones

def is_valid_domain(url):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https']

def main():
    rows = sheet.get_all_values()

    for idx, row in enumerate(rows[1:], start=2):  # Skip header, start at row 2
        url = row[URL_COL - 1]
        status = row[STATUS_COL - 1] if len(row) >= STATUS_COL else ''

        if status.strip().lower() == 'done' or not url.strip():
            continue

        if not is_valid_domain(url):
            sheet.update_cell(idx, STATUS_COL, 'Invalid URL')
            continue

        print(f"Processing row {idx}: {url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html = response.text

            emails, phones = extract_contacts(html)

            email_str = ', '.join(emails) if emails else ''
            phone_str = ', '.join(phones) if phones else ''

            sheet.update_cell(idx, EMAIL_COL, email_str)
            sheet.update_cell(idx, PHONE_COL, phone_str)
            sheet.update_cell(idx, STATUS_COL, 'Done')

        except Exception as e:
            print(f"Error on row {idx}: {e}")
            sheet.update_cell(idx, STATUS_COL, f"Error: {str(e)}")

        time.sleep(5)  # Be polite

if __name__ == '__main__':
    main()
