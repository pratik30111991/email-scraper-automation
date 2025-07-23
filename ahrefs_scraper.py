import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

INPUT_FILE = "ahrefs_data.csv"
OUTPUT_FILE = "ahrefs_data.csv"  # same file (overwrite)

# Simple regex patterns
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(\+?\d{1,3}?[-.\s]??\(?\d{2,4}?\)?[-.\s]??\d{3,5}[-.\s]??\d{3,5})')

# Columns
URL_COLUMN = "Referring page URL"
LIST_GROUP_COL = "Links in group"
EMAIL_COLUMN = "Extracted Email"
PHONE_COLUMN = "Extracted Phone"

def extract_contact_info(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        text = soup.get_text()
        emails = EMAIL_REGEX.findall(text)
        phones = PHONE_REGEX.findall(text)

        # Return first email/phone or empty
        email = emails[0] if emails else ''
        phone = phones[0] if phones else ''
        return email, phone
    except Exception as e:
        print(f"[ERROR] Failed for {url}: {e}")
        return '', ''

def main():
    with open(INPUT_FILE, "r", encoding="utf-8", newline='') as infile:
        reader = list(csv.DictReader(infile))
        fieldnames = reader[0].keys()

        # Prepare new fieldnames
        if EMAIL_COLUMN not in fieldnames:
            fieldnames = list(fieldnames) + [EMAIL_COLUMN, PHONE_COLUMN]

    # Write output back to CSV
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            url = row.get(URL_COLUMN, '').strip()
            existing_email = row.get(EMAIL_COLUMN, '').strip()
            existing_phone = row.get(PHONE_COLUMN, '').strip()

            # Skip if already extracted
            if existing_email or existing_phone:
                print(f"[SKIP] Already scraped: {url}")
                writer.writerow(row)
                continue

            print(f"[SCRAPE] {url}")
            email, phone = extract_contact_info(url)
            row[EMAIL_COLUMN] = email
            row[PHONE_COLUMN] = phone
            writer.writerow(row)
            time.sleep(2)  # polite scraping

    print("\n✅ Done. Results saved to:", OUTPUT_FILE)

if __name__ == "__main__":
    main()
