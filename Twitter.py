import json
import requests
from tinydb import TinyDB, Query
import datetime


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

    # Makes requests to the Twitter API
    # Takes in an endpoint and a dict of query parameters
    # Returns API response as JSON, or null if the request failed
    def fetch(self, endpoint, queryParams):
        headers = {"Authorization": "Bearer " + self.BEARER_TOKEN}
        res = requests.get(endpoint, headers=headers, params=queryParams)
        return res.json() if res.status_code == 200 else None

    # Helper for making requests to the user endpoint of the Twitter API
    def fetchUserData(self, username):
        params = {'usernames': username,
                  'user.fields': 'created_at',
                  'expansions': 'pinned_tweet_id',
                  'tweet.fields': 'author_id,created_at'
                  }
        return self.fetch('https://api.twitter.com/2/users/by', params)

    # Fetches all the tweets for a given Twitter account from the last 24 hours
    def fetchTweets(self, username):
        params = {
            'max_results': 100,
            'start_time': self.timestamp(rewind=1),
            'end_time': self.timestamp()
        }
        return self.fetch('https://api.twitter.com/2/users/{}/tweets'.format(self.getUserID(username)), params)

    # Generates an RFC3339 timestamp.
    # Returns the current timestamp if the rewind field is not provided, else
    #   returns a timestamp for the current time minus {rewind} days
    def timestamp(self, rewind=0):
        timestamp = datetime.datetime.now() - datetime.timedelta(days=rewind)
        timestamp = timestamp.replace(microsecond=0)
        timestamp = timestamp.isoformat('T') + 'Z'
        return timestamp

    # Gets userID from username
    # An entry for this user must exist in the db
    def getUserID(self, username):
        entry = self.ACCOUNTS.search(Query().handle == username)
        return entry[0]['id'] if len(entry) == 1 else None

    # Updates the database file to store account information for all inserted users
    def updateAccountTable(self, FIELD):
        for accountEntry in self.ACCOUNTS:
            # skip over entries we've already fetched user IDs for
            if 'id' in accountEntry.keys():
                continue
            handle = accountEntry['handle']
            # fetch user ID and upsert the DB entry
            data = self.fetchUserData(handle)
            if data:
                data = data['data'][0]
                accountEntry['name'] = data['name']
                accountEntry['id'] = data['id']
                self.ACCOUNTS.upsert(accountEntry, FIELD.handle == handle)


if __name__ == "__main__":
    twitter = Twitter()
    print(twitter.fetchTweets('reuters'))
