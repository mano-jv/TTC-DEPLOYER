import os
import xlrd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from db import db
import io
import shutil

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import db

SCOPES = ['https://www.googleapis.com/auth/drive']


def push_csv_to_drive(active_sprint_name, folder_id):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds, static_discovery=False)
        file_metadata = {'name': 'SprintRelease: ' + active_sprint_name,
                         'driveId': '0AGbIkEvxGd9tUk9PVA',
                         'parents': [folder_id],
                         'mimeType': 'application/vnd.google-apps.spreadsheet'}
        media = MediaFileUpload('Book.xlsx',
                                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        file = service.files().create(body=file_metadata, media_body=media,
                                      supportsAllDrives=True, fields='id').execute()

        return file.get("id")
    except HttpError as err:
        print(err)


def foo():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds, static_discovery=False)
    '''results = service.files().list(
        pageSize=1000).execute()
    items = results.get('files', [])

    # print a list of files

    print("Here's a list of files: \n")
    print(*items, sep="\n", end="\n\n")
    '''
    request = service.files().export_media(fileId="1tOZrwouZ3HQ3uTnCTn5OhBJm_LkDdvGHHkp6OBhS69s",
                                           mimeType='text/csv')
    fh = io.BytesIO()
    # Initialise a downloader object to download the file
    downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
    done = False
    try:
        # Download the data in chunks
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        # Write the received data to the file
        with open("download.csv", 'w') as f:
            f.write(fh.getvalue().decode('ascii'))

        print(fh.getvalue())
        print("File Downloaded")
    except Exception as e:
        print(e)


def get_corresponding_team_folder_id(team_name):
    response = db.jira_collection.find_one({"team_name": team_name.lower()}, {"folder_id": 1})
    return response["folder_id"]

foo()