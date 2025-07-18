# import os.path
# import base64
# import re
# from google.auth.transport.requests import Request 
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

# # Scopes give read-only Gmail access
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# def get_gmail_service():
#     creds = None
#     TOKEN_PATH = 'token.json'

#     # Check if token already exists
#     if os.path.exists(TOKEN_PATH):
#         creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

#     # If no token or token invalid, start OAuth login flow
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 '/etc/secrets/credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0)

#         # Save token to a writable path (not /etc/secrets/)
#         with open(TOKEN_PATH, 'w') as token:
#             token.write(creds.to_json())

#     # Build Gmail service
#     service = build('gmail', 'v1', credentials=creds)
#     return service

# def read_recent_emails():
#     service = get_gmail_service()
#     results = service.users().messages().list(userId='me', maxResults=5).execute()
#     messages = results.get('messages', [])

#     for msg in messages:
#         msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
#         payload = msg_data['payload']
#         headers = payload.get('headers')
#         subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
#         snippet = msg_data.get('snippet', '')
#         print(f"\n📨 Subject: {subject}\n📝 Snippet: {snippet}\n")

# if __name__ == '__main__':
#     read_recent_emails()




# import os
# import json
# import base64
# import re
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

# # Scopes give read-only Gmail access
# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# # Paths (use writable path for token.json)
# TOKEN_PATH = 'token.json'
# CREDENTIALS_PATH = 'credentials.json'  # Place your client_secret.json here

# def get_gmail_service():
#     creds = None

#     # Try to load existing token.json (handle empty or corrupted file)
#     if os.path.exists(TOKEN_PATH):
#         try:
#             creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
#         except (json.JSONDecodeError, ValueError):
#             creds = None  # Force re-authentication

#     # If no valid creds, authenticate
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             # Use credentials.json for OAuth flow
#             flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
#             creds = flow.run_local_server(port=0)  # Opens browser for login

#         # Save token.json for next time (only for local machine)
#         with open(TOKEN_PATH, 'w') as token_file:
#             token_file.write(creds.to_json())

#     # Build and return Gmail API service
#     service = build('gmail', 'v1', credentials=creds)
#     return service

# def read_recent_emails():
#     service = get_gmail_service()
#     results = service.users().messages().list(userId='me', maxResults=5).execute()
#     messages = results.get('messages', [])

#     for msg in messages:
#         msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
#         payload = msg_data['payload']
#         headers = payload.get('headers', [])
#         subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
#         snippet = msg_data.get('snippet', '')
#         print(f"\n📨 Subject: {subject}\n📝 Snippet: {snippet}\n")

# if __name__ == '__main__':
#     read_recent_emails()


import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'

gmail_service = None  # Cache the service so we don't re-login every time

def get_gmail_service():
    global gmail_service
    if gmail_service:
        return gmail_service  # Reuse existing session

    creds = None

    # Only load token.json if we're on local machine
    if os.path.exists(TOKEN_PATH) and not os.environ.get("RENDER"):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except (json.JSONDecodeError, ValueError):
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token.json only locally, not on Render
        if not os.environ.get("RENDER"):
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())

    gmail_service = build('gmail', 'v1', credentials=creds)
    return gmail_service
