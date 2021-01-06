import Twitter
import Gmail
import sklearn
from tinydb import TinyDB, Query
import time

DATABASE_PATH = 'data/db.json'
TWEETS_TABLE = 'tweets'
ACCOUNTS_TABLE = 'accounts'
SECONDS_PER_DAY = 86400

# Checks whether cached tweets are from > 24 hours ago.
# If tweets are older than 24 hours, wipes current cache and
# fetches new data from Twitter
def fetchLatestTweets(twitter, db):
    # check timestamp
    tweets_table = db.table(TWEETS_TABLE)
    tweets_table = tweets_table.get(doc_id=len(tweets_table))
    if tweets_table is not None and not timestampExpired(float(tweets_table.get('timestamp'))):
        return
    # create new entry
    tweets = {
        'timestamp': time.time(),
        'tweets': []
    }
    for user in db.table(ACCOUNTS_TABLE):
        # get handle
        if not 'handle' in user.keys():
            continue
        handle = user.get('handle')
        # fetch tweets
        res = twitter.fetchTweets(handle)
        if res is not None:
            # add tweets to dict
            tweets['tweets'].append({
                'handle': handle,
                'tweets': [entry['text'] for entry in res['data']]
            })
    # insert new entry into tweets table
    db.table(TWEETS_TABLE).insert(tweets)

def timestampExpired(old, now=time.time()):
    return (now - old) > SECONDS_PER_DAY

def extractKeywords():
    pass


def clusterTweets():
    pass


def scoreClusters():
    pass


def draftEmail():
    pass


if __name__ == "__main__":
    twitter = Twitter.Twitter()  # init twitter
    gmail = Gmail.Gmail()   # init gmail
    db = TinyDB(DATABASE_PATH)

    fetchLatestTweets(twitter, db)

    # Extract category names from tweets

    # Cluster tweets

    # Score clusters

    # Send email
