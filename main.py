import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import re

# Authenticate with Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
gc = gspread.authorize(credentials)

# Your Google Sheet URL (ensure correct and shared with service account)
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1UlN2GJ30N-Cx__xKMT2mtOZZv2fxlOXf6kTfBfrqwNQ/edit#gid=0")
worksheet = sheet.worksheet("Scraped Data")

base_url = "https://www.ahrefs.com/blog/outreach-email-template/"
headers = {
    "User-Agent": "Mozilla/5.0"
}

def extract_email_and_phone(text):
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phones = re.findall(r'\+?\d[\d\s().-]{7,}\d', text)
    return emails, phones

def scrape_and_append():
    print("Starting scrape...")

    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    all_text = soup.get_text()
    emails, phones = extract_email_and_phone(all_text)

    row = [base_url, ", ".join(emails), ", ".join(phones)]
    worksheet.append_row(row)

    print("Scrape complete and saved to Google Sheet.")

scrape_and_append()
