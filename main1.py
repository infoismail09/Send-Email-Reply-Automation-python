import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import re
from env import Environ

# Path to your JSON credentials file downloaded from the Google Cloud Console
CREDENTIALS_FILE = Environ.CREDENTIALS_FILE

# The email address of the account you want to use
EMAIL_ADDRESS = Environ.EMAIL_ADDRESS

def create_service():
    # Load the credentials from the JSON file
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', [Environ.googleapisreadonly, Environ.googleapissend])
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, [Environ.googleapisreadonly, Environ.googleapimodify,  Environ.googleapissend])
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_messages(service, query):
    try:
        response = service.users().messages().list(userId=EMAIL_ADDRESS, q=query).execute()
        messages = response.get('messages', [])
        return messages
    except Exception as e:
        print(f'An error occurred: {e}')
        return []

def send_reply(service, message_id, reply_text):
    try:
        message = service.users().messages().get(userId=EMAIL_ADDRESS, id=message_id, format='full').execute()
        subject = None
        sender = None
        thread_id = message['threadId']
        email_body = ""

        for header in message['payload']['headers']:
            if header['name'] == 'Subject':
                subject = header['value']
            if header['name'] == 'From':
                sender_info = header['value']
                # Use regular expression to extract the email address from the sender info
                sender_match = re.search(r'<([^>]+)>', sender_info)
                if sender_match:
                    sender = sender_match.group(1)

        if 'body' in message['payload']:
            if 'data' in message['payload']['body']:
                email_body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

        if subject:
            if sender:
                # Create a reply message with the recipient's email address in the "To" field
                reply_message = {
                    'raw': base64.urlsafe_b64encode(
                        f"Subject: Re: {subject}\nTo: {sender}\nIn-Reply-To: {thread_id}\nReferences: {thread_id}\n\n{reply_text}\n\nOriginal Email:\n{email_body}".encode('utf-8')).decode('utf-8')
                }
                service.users().messages().send(userId=EMAIL_ADDRESS, body=reply_message).execute()
                print('Reply sent successfully.')
            else:
                print('Sender email address not found.')
        else:
            print('No subject found in the original message.')

    except Exception as e:
        print(f'An error occurred: {e}')

def main():
    query = 'is:unread subject:"Hi"'
    service = create_service()
    messages = list_messages(service, query)

    for message in messages:
        send_reply(service, message['id'], 'I had Confirmed')  

if __name__ == '__main__':
    main()
