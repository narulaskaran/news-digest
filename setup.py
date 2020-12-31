from os import path, mkdir
import Gmail
import Twitter
from tinydb import TinyDB, Query

GMAIL_CONFIG_PATH = 'config/gmail-credentials.json'
GMAIL_CREDENTIALS = {
    "installed": {
        "client_id": "INSERT HERE",
        "project_id": "INSERT HERE",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "INSERT HERE",
        "redirect_uris": [
            "urn:ietf:wg:oauth:2.0:oob",
            "http://localhost"
        ]
    }
}
TWITTER_CONFIG_PATH = 'config/twitter-credentials.json'
TWITTER_CREDENTIALS = {
    "api-key": "INSERT HERE",
    "api-secret": "INSERT HERE",
    "bearer-token": "INSERT HERE"
}
DB_PATH = 'data/db.json'


def check_twitter_auth():
    if not path.exists(TWITTER_CONFIG_PATH):
        init_credential_file(TWITTER_CONFIG_PATH, TWITTER_CREDENTIALS)
    else:
        Twitter.Twitter()


def check_gmail_auth():
    if not path.exists(GMAIL_CONFIG_PATH):
        init_credential_file(GMAIL_CONFIG_PATH, GMAIL_CREDENTIALS)
    else:
        Gmail.Gmail()


def init_db():
    if not path.exists(DB_PATH):
        mkdir('data')
        f = open(DB_PATH, 'w')
        f.write('')
        f.close()
    db = TinyDB(DB_PATH)


def init_credential_file(path, contents):
    f = open(path, 'w')
    f.write(contents)
    f.close()
    print("FILL IN CREDENTIALS AT " + path + ", THEN RERUN SETUP")

if __name__ == "__main__":
    check_twitter_auth()
    check_gmail_auth()
    init_db()
