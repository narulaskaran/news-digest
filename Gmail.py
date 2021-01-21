from __future__ import print_function
import pickle, os.path, base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class Gmail:
  def __init__(self):
    self.SENDER_ADDRESS = 'aqialert@narula.xyz'
    self.PICKLE_PATH = 'config/token.pickle'

    # authenticate
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(self.PICKLE_PATH):
        with open(self.PICKLE_PATH, 'rb') as token:
            creds = pickle.load(token)
    # If there are no valid credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'config/gmail-credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(self.PICKLE_PATH, 'wb') as token:
            pickle.dump(creds, token)

    self.SERVICE = build('gmail', 'v1', credentials=creds)

  def create_message(self, email, subject, body):
    message = MIMEText(body, 'html')
    message['to'] = email
    message['from'] = self.SENDER_ADDRESS
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
    return {'raw': raw_message.decode('utf-8')}

  def send_message(self, email, subject, body):
    try:
      encoded_message = self.create_message(email, subject, body)
      message = (self.SERVICE.users().messages().send(userId='me', body=encoded_message)
                .execute())
      print('Message Id: {}'.format(message['id']))
      return message
    except Exception as err:
      print("An error occurred while sending the email: {}".format(err))

if __name__ == "__main__":
    Gmail()