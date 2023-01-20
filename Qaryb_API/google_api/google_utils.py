from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from os import path
from Qaryb_API.settings import GOOGLE_SPREADSHEET_ID
from googleapiclient.discovery import build

parent_file_dir = path.abspath(path.join(path.dirname(__file__), ".."))

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/indexing',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/spreadsheets'
]


class GoogleUtils:
    def __init__(self):
        self.responses = []
        self.errors = []

    @staticmethod
    def get_or_create_google_credentials():
        # parent_file_dir + '/Qaryb_API/google_api/
        creds = None
        if path.exists(parent_file_dir + '/google_api/token.json'):
            creds = Credentials.from_authorized_user_file(
                parent_file_dir + '/google_api/token.json',
                GOOGLE_SCOPES
            )
            # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    parent_file_dir + '/google_api/secret.json',
                    GOOGLE_SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(parent_file_dir + '/google_api/token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def indexing_event(self, request_id, response, exception):
        if exception is not None:
            self.errors.append(exception)
        else:
            # ex
            # {
            #   'urlNotificationMetadata': {
            #     'url': 'https://qaryb.com/collections/blocnote/',
            #     'latestUpdate': {
            #       'url': 'https://qaryb.com/collections/blocnote/',
            #       'type': 'URL_UPDATED',
            #       'notifyTime': '2023-01-20T09:14:31.599080945Z'
            #     }
            #   }
            # }
            self.responses.append(response)

    def insert_sheet(self, data):
        credentials = self.get_or_create_google_credentials()
        service = build('sheets', 'v4', credentials=credentials)
        service.spreadsheets().values().append(
            spreadsheetId=GOOGLE_SPREADSHEET_ID,
            range="Sheet1!A:Z",
            body={
                "majorDimension": "ROWS",
                "values": data
            },
            valueInputOption="USER_ENTERED"
        ).execute()

    def index_pages(self, urls_to_index):
        credentials = self.get_or_create_google_credentials()
        service = build('indexing', 'v3', credentials=credentials)
        batch = service.new_batch_http_request(callback=self.indexing_event)
        for url, api_type in urls_to_index.items():
            batch.add(
                service.urlNotifications().publish(
                    body={"url": url, "type": api_type}
                )
            )
        batch.execute()
