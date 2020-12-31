import json
import requests


class Twitter:
    def __init__(self):
        with open('config/twitter-credentials.json') as config:
            # load keys
            config = json.load(config)
            self.API_KEY = config['api-key']
            self.API_SECRET = config['api-secret']
            self.BEARER_TOKEN = config['bearer-token']
            # make test request
            status_code, res = self.fetchUserData('jack')
            if status_code == 200:
                print('Successful test request!')
            else:
                print('Error connecting to the Twitter API :(\nStatus Code: {}\n{}'.format(
                    status_code, res))

    def fetch(self, endpoint, queryParams):
        headers = {"Authorization": "Bearer " + self.BEARER_TOKEN}
        res = requests.get(endpoint, headers=headers, params=queryParams)
        return res.status_code, res.json()

    def fetchUserData(self, username):
        params = {'usernames': username,
                  'user.fields': 'created_at',
                  'expansions': 'pinned_tweet_id',
                  'tweet.fields': 'author_id,created_at'}
        return self.fetch('https://api.twitter.com/2/users/by', params)


if __name__ == "__main__":
    Twitter()
