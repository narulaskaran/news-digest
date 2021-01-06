# personal packages
import Twitter
import Gmail
import Tweet
# db packages
from tinydb import TinyDB, Query
import time
# data/ML packages
import sklearn

# constants
DATABASE_PATH = 'data/db.json'
TWEETS_TABLE = 'tweets'
ACCOUNTS_TABLE = 'accounts'
SECONDS_PER_DAY = 86400

# Checks whether last-fetched tweets are from > 24 hours ago.
# If tweets are older than 24 hours, fetches the latest ones from Twitter
#   and inserts them into the database
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

# Returns true if old timestamp is from > 24 hours ago, false otherwise
def timestampExpired(old, now=time.time()):
    return (now - old) > SECONDS_PER_DAY

# Sanitizes text by removing special unicode and lowering case
def pre_process(text):
    text = text.lower()
    text = text.encode('ascii', 'ignore').decode("utf-8")
    return text

def parseTweets(db):
    # get most recent set of tweets
    tweets_table = db.table(TWEETS_TABLE)
    tweets_table = tweets_table.get(doc_id=len(tweets_table))
    if 'tweets' not in tweets_table.keys():
        return None
    tweets_table = tweets_table['tweets']
    tweets = []
    for entry in tweets_table:
        handle = entry['handle']
        tweets.append([Tweet.Tweet(handle,pre_process(tweet)) for tweet in entry['tweets']])
    return tweets

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

    # Process data
    dataset = parseTweets(db)

    # Extract category names from tweets

    # Cluster tweets

    # Score clusters

    # Send email
