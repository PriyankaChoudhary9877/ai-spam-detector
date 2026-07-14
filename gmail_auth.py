import os
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

TOKEN_PATH = "token.json"
CREDENTIALS_PATH = "credentials.json"

gmail_service = None


def get_gmail_service():
    global gmail_service

    if gmail_service:
        return gmail_service

    creds = None

    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(
                TOKEN_PATH,
                SCOPES
            )
        except (ValueError, json.JSONDecodeError):
            creds = None

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

    gmail_service = build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False
    )

    return gmail_service