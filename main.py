import re
import time
import gspread
import requests
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

# === SETTINGS ===
GOOGLE_SHEET_NAME = "YOUR_SHEET_NAME"
WORKSHEET_NAME = "Sheet1"
SERVICE_ACCOUNT_FILE = "credentials.json"
MAX_LINKS_PER_RUN = 1000  # Or set as needed
WAIT_SECONDS_BETWEEN_REQUESTS = 2  # Avoid blocking

# === Setup Google Sheet ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(GOOGLE_SHEET_NAME).worksheet(WORKSHEET_NAME)

# === Load all data ===
data = sheet.get_all_values()
headers = data[0]
rows = data[1:]

# === Column Indexes ===
try:
    url_col = headers.index("Referring page URL")
    status_col = headers.index("Status")
except ValueError:
    headers.append("Status")
    status_col = len(headers) - 1
    sheet.update_cell(1, status_col + 1, "Status")

if "Email ID" not in headers:
    headers.append("Email ID")
    sheet.update_cell(1, len(headers), "Email ID")
email_col = headers.index("Email ID")

if "Contact Number" not in headers:
    headers.append("Contact Number")
    sheet.update_cell(1, len(headers), "Contact Number")
phone_col = headers.index("Contact Number")

# === Helper Functions ===
def extract_emails(text):
    return list(set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)))

def extract_phones(text):
    return list(set(re.findall(r"\+?\d[\d\s\-()]{8,}", text)))

# === Main Loop ===
processed = 0
for i, row in enumerate(rows):
    sheet_row_num = i + 2
    status = row[status_col] if status_col < len(row) else ""

    if status.strip().lower() == "done":
        continue

    url = row[url_col] if url_col < len(row) else ""
    if not url.strip():
        continue

    print(f"🔍 Visiting: {url}")
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()

        emails = extract_emails(text)
        phones = extract_phones(text)

        email_str = ", ".join(emails)[:300]
        phone_str = ", ".join(phones)[:300]

        # Update the row
        sheet.update_cell(sheet_row_num, email_col + 1, email_str)
        sheet.update_cell(sheet_row_num, phone_col + 1, phone_str)
        sheet.update_cell(sheet_row_num, status_col + 1, "Done")

    except Exception as e:
        print(f"❌ Error on row {sheet_row_num}: {e}")
        sheet.update_cell(sheet_row_num, status_col + 1, "Failed")

    processed += 1
    if processed >= MAX_LINKS_PER_RUN:
        break
    time.sleep(WAIT_SECONDS_BETWEEN_REQUESTS)

print("✅ Done.")
