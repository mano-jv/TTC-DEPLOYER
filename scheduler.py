import io
import shutil

import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from pytz import timezone
import db
from datetime import datetime

### AUTHORIZATION AND HEADER SECTION
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Basic *********"
}

scopes = ['https://www.googleapis.com/auth/chat.bot, https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'chatCredentials.json', scopes)
changes_url = "https://trimbletransportation.freshservice.com/api/v2/changes/"
chat_service = build('drive', 'v3', http=credentials.authorize(Http()))


def check_approval_status():
    ###Query Ticket Collection for approval status 0
    results = list(db.tickets_collection.find({"approval_status": 0}, {"_id": 1, "ticket_id": 1, "space_name": 1}))

    for doc in results:
        approval_response = requests.get(
            changes_url + doc["ticket_id"], headers=headers).json()
        if approval_response["change"]["approval_status"] == 1:
            send_message(doc["space_name"], "Fresh Service Ticket Approved.")
            db.tickets_collection.update_one({"_id": doc["_id"]}, {"$set": {"approval_status": 1}})

    current_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')
    ###Query Ticket Collection for date and time
    response = list(
        db.tickets_collection.find({"flag": 0}, {"_id": 1, "date": 1, "time": 1, "ticket_id": 1, "space_name": 1}))
    for doc in response:
        if int((datetime.strptime(doc["date"] + " " + doc["time"],
                              "%Y-%m-%d %H:%M:%S") - datetime.strptime(current_time,
                                                                       "%Y-%m-%d %H:%M:%S")).total_seconds() // 60) == 5:
            msg = "Deployment is scheduled in 5 mins"
            if (requests.get(
                    changes_url + doc["ticket_id"], headers=headers).json()["change"]["approval_status"] != 1):
                msg = msg + "\nTicket Yet to be Approved"
            send_message(doc["space_name"], msg)
            db.tickets_collection.update_one({"_id": doc["_id"]}, {"$set": {"flag": 1}})

def fun():
    list = chat_service.spaces().messages().attachments().attachmentDataRef().get(
        name = "ClxzcGFjZXMvdjBZT2drQUFBQUUvbWVzc2FnZXMvQW9odTlMR181TWMuQW9odTlMR181TWMvYXR0YWNobWVudHMvQUFUVWYtSWxIeDZ1aTR4LTFVU2FHYmt1VEhZSw=="
    ).execute()
    print(list)

def foo():
    request = chat_service.files().get_media(fileId="1uN5OU7USOXt89sFXIO_4ZhefyGQctkKOoRdlJSttffQ").execute()
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
        with open("download", 'wb') as f:
            shutil.copyfileobj(fh, f)
        print("File Downloaded")
    except:
        pass

def send_message(space_name, msg):
    chat_service.spaces().messages().create(
        parent=space_name,
        # The message to create.
        body={'text': msg}
    ).execute()

foo()


