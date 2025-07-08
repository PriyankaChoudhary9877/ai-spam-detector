import os.path
import base64
import re
from google.auth.transport.requests import Request 
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes give read-only Gmail access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    TOKEN_PATH = 'token.json'

    # Check if token already exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no token or token invalid, start OAuth login flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/etc/secrets/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token to a writable path (not /etc/secrets/)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service

def read_recent_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])

    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        payload = msg_data['payload']
        headers = payload.get('headers')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        snippet = msg_data.get('snippet', '')
        print(f"\n📨 Subject: {subject}\n📝 Snippet: {snippet}\n")

if __name__ == '__main__':
    read_recent_emails()
