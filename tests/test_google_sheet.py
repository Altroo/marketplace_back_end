from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1e1gA_7D23B_3Jje15kJHkxxPwLK9v7lztSL8ZZ98O8o'


def get_or_create_credentials(scopes):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'google.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def main():
    rows = [
        ["Yooy", "Altroo", "063322112", "ma-insta", "9-12"],
    ]

    # -----------

    credentials = get_or_create_credentials(scopes=SCOPES)  # or use GoogleCredentials.get_application_default()
    service = build('sheets', 'v4', credentials=credentials)
    service.spreadsheets().values().append(
        spreadsheetId=SAMPLE_SPREADSHEET_ID,
        range="Sheet1!A:Z",
        body={
            "majorDimension": "ROWS",
            "values": rows
        },
        valueInputOption="USER_ENTERED"
    ).execute()


if __name__ == '__main__':
    main()
