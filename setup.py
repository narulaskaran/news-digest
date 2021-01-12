from os import path, mkdir
import Gmail
import Twitter
from tinydb import TinyDB
import json
from urllib import request

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
STOP_WORD_LIST_URL = 'https://raw.githubusercontent.com/kavgan/stop-words/master/minimal-stop.txt'
FIGURES_DIR_PATH = 'figures'


def init_credential_file(path, contents):
    f = open(path, 'w')
    f.write(contents)
    f.close()
    print("FILL IN CREDENTIALS AT " + path + ", THEN RERUN SETUP")


if __name__ == "__main__":
    # db init
    if not path.exists(DB_PATH):
        if not path.isdir('./data/'):
            mkdir('data')
        f = open(DB_PATH, 'w')
        f.write('')
        f.close()
    
    # init account and tweet tables
    db = TinyDB(DB_PATH)
    accounts_table = db.table('accounts')
    tweets_table = db.table('tweets')

    # init accounts table with starter twitter handles
    with open('./config/config.json') as config:
        config = json.load(config)
        accounts_table.insert_multiple(
            [{'handle': handle} for handle in config['accounts']])

    # gmail auth
    if not path.exists(GMAIL_CONFIG_PATH):
        init_credential_file(GMAIL_CONFIG_PATH, GMAIL_CREDENTIALS)
    else:
        Gmail.Gmail()

    # twitter auth
    if not path.exists(TWITTER_CONFIG_PATH):
        init_credential_file(TWITTER_CONFIG_PATH, TWITTER_CREDENTIALS)
    else:
        Twitter.Twitter()

    # download stop-word list
    request.urlretrieve(STOP_WORD_LIST_URL, 'data/stop-words.txt')

    # create dir for figures
    if not path.isdir(FIGURES_DIR_PATH):
        mkdir(FIGURES_DIR_PATH)