import gspread
import re
import requests
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from time import sleep

# -------------- CONFIGURATION --------------
SPREADSHEET_NAME = "Your Google Sheet Name Here"
WORKSHEET_NAME = "Sheet1"  # or change to match your sheet
LINKS_COLUMN_HEADER = "Links in group"
EMAIL_COLUMN_HEADER = "Email ID"
PHONE_COLUMN_HEADER = "Contact Number"
STATUS_COLUMN_HEADER = "Status"
MAX_PER_RUN = 50  # Change this if you want more per run
SLEEP_BETWEEN = 5  # seconds delay between scraping each row
# ------------------------------------------

# Google Sheets API Auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)
data = sheet.get_all_records()

# Get column indexes
headers = sheet.row_values(1)
link_idx = headers.index(LINKS_COLUMN_HEADER)
email_idx = link_idx + 2
phone_idx = link_idx + 3
status_idx = headers.index(STATUS_COLUMN_HEADER)

# Ensure headers exist
if len(headers) <= phone_idx:
    sheet.update_cell(1, email_idx + 1, EMAIL_COLUMN_HEADER)
    sheet.update_cell(1, phone_idx + 1, PHONE_COLUMN_HEADER)

done_count = 0

# Start processing
for row_num, row in enumerate(data, start=2):
    if row.get(STATUS_COLUMN_HEADER, "").strip().lower() == "done":
        continue
    if not row.get(LINKS_COLUMN_HEADER):
        continue

    url = row[LINKS_COLUMN_HEADER]
    print(f"Processing row {row_num}: {url}")
    
    try:
        # Fetch the page
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        # Extract email
        emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)))
        email = emails[0] if emails else ""

        # Extract phone number
        phones = list(set(re.findall(r"\+?\d[\d\s\-\(\)]{8,}\d", text)))
        phone = phones[0] if phones else ""

        # Update sheet
        if email:
            sheet.update_cell(row_num, email_idx + 1, email)
        if phone:
            sheet.update_cell(row_num, phone_idx + 1, phone)
        sheet.update_cell(row_num, status_idx + 1, "Done")
        print(f"✅ Done: {email} | {phone}")

    except Exception as e:
        print(f"❌ Error on row {row_num}: {str(e)}")
        sheet.update_cell(row_num, status_idx + 1, "Error")
    
    done_count += 1
    if done_count >= MAX_PER_RUN:
        print("✅ Max limit reached for this run.")
        break
    sleep(SLEEP_BETWEEN)

print("✅ All done.")
