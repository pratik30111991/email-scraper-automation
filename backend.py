from flask import Flask, request, send_file
import gspread
import io
import os
import json
from datetime import datetime
from pytz import timezone
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
TZ = timezone('Asia/Kolkata')

@app.route('/track')
def track():
    try:
        sheet_name = request.args.get('sheet')
        row = int(request.args.get('row'))
        email_param = request.args.get('email')

        if not sheet_name or not row or not email_param:
            return '', 204

        creds_json = json.loads(os.environ['GOOGLE_JSON'])
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        client = gspread.authorize(creds)

        sheet = client.open_by_key(os.environ['SHEET_ID'])
        worksheet = sheet.worksheet(sheet_name)
        email_in_sheet = worksheet.cell(row, 3).value.strip()  # column 3 = "Email ID"

        if email_in_sheet != email_param:
            return '', 204

        open_col = worksheet.cell(row, 10).value  # column 10 = "Open?"
        if open_col != 'Yes':
            worksheet.update_cell(row, 10, 'Yes')  # Open?
            worksheet.update_cell(row, 11, datetime.now(TZ).strftime('%d/%m/%Y %H:%M:%S'))  # Open Timestamp

        pixel = io.BytesIO(b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\xff\x00\xff\xff\xff\x00\x00\x00\x21\xf9'
                           b'\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00'
                           b'\x3b')
        return send_file(pixel, mimetype='image/gif')

    except Exception:
        return '', 204

@app.route('/')
def home():
    return 'Tracking Server Running ✅'

if __name__ == '__main__':
    app.run(debug=False)
