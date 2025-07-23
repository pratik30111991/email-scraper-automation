import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup
import re
import time

# === AUTH SETUP ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# === CONFIG ===
SHEET_ID = "1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ"
SHEET_NAME = "Sheet1"
MAX_LINKS_PER_RUN = 25

# === FETCH SHEET ===
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
headers = sheet.row_values(1)
rows = sheet.get_all_values()[1:]

# === FIND EMAIL/CELL COL INDEXES ===
link_col_idx = headers.index("Referring page URL") + 1
group_col_idx = headers.index("Links in group") + 1
email_col_idx = group_col_idx + 2  # Leave one blank column
phone_col_idx = group_col_idx + 3

# === EMAIL & PHONE EXTRACTORS ===
def extract_email(text):
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return emails[0] if emails else "Not Found"

def extract_phone(text):
    phones = re.findall(r"\+?\d[\d\s\-()]{7,}\d", text)
    return phones[0] if phones else "Not Found"

# === SCRAPE FUNCTION ===
def scrape_info(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        email = extract_email(text)
        phone = extract_phone(text)
        return email, phone
    except Exception:
        return "Error", "Error"

# === PROCESS ROWS ===
processed = 0
for i, row in enumerate(rows, start=2):  # start=2 because row 1 is header
    if processed >= MAX_LINKS_PER_RUN:
        break

    url = row[link_col_idx - 1].strip()
    email_cell = sheet.cell(i, email_col_idx).value
    phone_cell = sheet.cell(i, phone_col_idx).value

    if email_cell or phone_cell:
        continue  # Skip already processed

    if not url or not url.startswith("http"):
        continue

    print(f"Processing row {i}: {url}")
    email, phone = scrape_info(url)
    sheet.update_cell(i, email_col_idx, email)
    sheet.update_cell(i, phone_col_idx, phone)

    processed += 1
    time.sleep(2)  # Be polite
