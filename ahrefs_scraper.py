import re
import time
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse

# ------------------------
# Google Sheets Setup
# ------------------------
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(credentials)

sheet_url = 'https://docs.google.com/spreadsheets/d/1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ/edit'
doc = gc.open_by_url(sheet_url)
sheet = doc.worksheet('Sheet1')

# ------------------------
# Column Configuration
# ------------------------
URL_COL = 3      # Referring page URL
STATUS_COL = 39  # AM = Status
EMAIL_COL = 37   # AK = Email ID
PHONE_COL = 38   # AL = Contact Number

# ------------------------
# Visibility Filter for BS4
# ------------------------
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

# ------------------------
# Extract visible text only
# ------------------------
def extract_contacts(html):
    soup = BeautifulSoup(html, "html.parser")
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    text = u" ".join(t.strip() for t in visible_texts)

    emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))
    phones = list(set(re.findall(r"\+?\d[\d\s\-().]{7,}\d", text)))

    return emails, phones

# ------------------------
# Validate URLs
# ------------------------
def is_valid_domain(url):
    parsed = urlparse(url)
    return parsed.scheme in ['http', 'https']

# ------------------------
# Main Processing Loop
# ------------------------
def main():
    rows = sheet.get_all_values()

    for idx, row in enumerate(rows[1:], start=2):  # Skip header row
        url = row[URL_COL - 1]
        status = row[STATUS_COL - 1] if len(row) >= STATUS_COL else ''

        if status.strip().lower() == 'done' or not url.strip():
            continue

        if not is_valid_domain(url):
            sheet.update_cell(idx, STATUS_COL, 'Invalid URL')
            continue

        print(f"[{idx}] Fetching: {url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            emails, phones = extract_contacts(response.text)

            email_str = ', '.join(emails) if emails else ''
            phone_str = ', '.join(phones) if phones else ''

            sheet.update_cell(idx, EMAIL_COL, email_str)
            sheet.update_cell(idx, PHONE_COL, phone_str)
            sheet.update_cell(idx, STATUS_COL, 'Done')

        except Exception as e:
            print(f"[ERROR] Row {idx}: {e}")
            sheet.update_cell(idx, STATUS_COL, f"Error: {str(e)}")

        time.sleep(5)  # polite scraping

if __name__ == '__main__':
    main()
