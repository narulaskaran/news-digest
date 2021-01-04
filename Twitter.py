import json
import requests
from tinydb import TinyDB, Query

class Twitter:
    def __init__(self):
        with open('config/twitter-credentials.json') as config:
            # load keys
            config = json.load(config)
            self.API_KEY = config['api-key']
            self.API_SECRET = config['api-secret']
            self.BEARER_TOKEN = config['bearer-token']
            # make test request
            res = self.fetchUserData('jack')
            if res:
                print('Successful test request!')
            else:
                print('Error connecting to the Twitter API :(')
            # load db
            self.DB = TinyDB('data/db.json')
            self.ACCOUNTS = self.DB.table('accounts')
            self.updateAccountTable(Query())

    def fetch(self, endpoint, queryParams):
        headers = {"Authorization": "Bearer " + self.BEARER_TOKEN}
        res = requests.get(endpoint, headers=headers, params=queryParams)
        return res.json() if res.status_code == 200 else null

    def fetchUserData(self, username):
        params = {'usernames': username,
                  'user.fields': 'created_at',
                  'expansions': 'pinned_tweet_id',
                  'tweet.fields': 'author_id,created_at'}
        return self.fetch('https://api.twitter.com/2/users/by', params)

    def updateAccountTable(self, FIELD):
        for accountEntry in self.ACCOUNTS:
            handle = accountEntry['handle']
            data = self.fetchUserData(handle)
            if data:
                data = data['data'][0]
                accountEntry['name'] = data['name']
                accountEntry['id'] = data['name']
                self.ACCOUNTS.upsert(accountEntry, FIELD.handle == handle)

if __name__ == "__main__":
    Twitter()
