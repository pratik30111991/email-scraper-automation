import os
import re
import json
import time
import gspread
import requests
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# Google Sheet setup
SHEET_ID = "1S29IoI97zph9oouwlsA7siFA4cymh-dB6cX0S5yjKtQ"
SHEET_NAME = "Sheet1"  # or change based on your actual sheet name
LAST_ROW_TRACKER = "Row_Tracker"

# Authenticate
def get_gspread_client():
    creds_json = os.getenv("GOOGLE_JSON")
    creds = json.loads(creds_json)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
    return gspread.authorize(credentials)

# Email and phone regex
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\+?\d[\d\s().-]{7,}\d")

def extract_contact_info(url, browser):
    try:
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=30000)
        time.sleep(3)
        content = page.content()
        text = BeautifulSoup(content, "html.parser").get_text()
        emails = EMAIL_REGEX.findall(text)
        phones = PHONE_REGEX.findall(text)
        context.close()
        return (emails[0] if emails else "", phones[0] if phones else "")
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ("", "")

def main():
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    data = sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    # Get the column indices
    url_col = headers.index("Referring page URL")
    insert_after = headers.index("Links in group")
    email_col = insert_after + 2
    phone_col = insert_after + 3

    # Ensure headers exist
    if len(headers) <= phone_col:
        for _ in range(phone_col - len(headers) + 1):
            headers.append("")
        headers[email_col] = "Email ID"
        headers[phone_col] = "Contact Number"
        sheet.update("A1", [headers])

    # Get the last processed row from a hidden tracker tab
    try:
        tracker_sheet = client.open_by_key(SHEET_ID).worksheet(LAST_ROW_TRACKER)
        last_row = int(tracker_sheet.acell("A1").value)
    except:
        tracker_sheet = client.open_by_key(SHEET_ID).add_worksheet(title=LAST_ROW_TRACKER, rows="1", cols="1")
        tracker_sheet.update("A1", "1")
        last_row = 1

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for i, row in enumerate(rows[last_row:], start=last_row + 2):  # +2 because data[0] = headers
            if len(row) <= url_col or not row[url_col].strip():
                continue

            url = row[url_col].strip()
            print(f"Scraping Row {i}: {url}")
            email, phone = extract_contact_info(url, browser)

            if email or phone:
                sheet.update_cell(i, email_col + 1, email)
                sheet.update_cell(i, phone_col + 1, phone)

            tracker_sheet.update("A1", str(i - 1))
            time.sleep(2)

        browser.close()

if __name__ == "__main__":
    main()
