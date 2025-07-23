import re
import time
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse

# Google Sheets Setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(credentials)

# Google Sheet details
sheet_url = 'https://docs.google.com/spreadsheets/d/1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ/edit'
worksheet_name = 'Sheet1'
sheet = gc.open_by_url(sheet_url).worksheet(worksheet_name)

# Column Numbers (1-indexed)
URL_COL = 3       # "Referring page URL"
EMAIL_COL = 37    # Column AK
PHONE_COL = 38    # Column AL
STATUS_COL = 39   # Column AM

# Regex patterns for email and phone
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(?:(?:\+|00)\d{1,3})?[\s\-.(]*\d{2,4}[\s\-.)]*\d{3,5}[\s\-]*\d{3,5}"

def extract_contacts(html):
    emails = list(set(re.findall(EMAIL_REGEX, html)))
    phones = list(set(re.findall(PHONE_REGEX, html)))
    return emails, phones

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https']

def main():
    rows = sheet.get_all_values()

    for i, row in enumerate(rows[1:], start=2):  # Skip header row
        url = row[URL_COL - 1].strip()
        status = row[STATUS_COL - 1].strip() if len(row) >= STATUS_COL else ''

        if status.lower() == 'done' or not url:
            continue

        if not is_valid_url(url):
            sheet.update_cell(i, STATUS_COL, 'Invalid URL')
            continue

        print(f"[{i}] Scraping: {url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            html = response.text

            emails, phones = extract_contacts(html)

            email_str = ', '.join(emails) if emails else ''
            phone_str = ', '.join(phones) if phones else ''

            sheet.update_cell(i, EMAIL_COL, email_str)
            sheet.update_cell(i, PHONE_COL, phone_str)
            sheet.update_cell(i, STATUS_COL, 'Done')

        except Exception as e:
            print(f"[{i}] Error: {e}")
            sheet.update_cell(i, STATUS_COL, f"Error: {str(e)}")

        time.sleep(5)  # Be polite to websites

if __name__ == "__main__":
    main()
