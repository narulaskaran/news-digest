# personal packages
import Twitter
import Gmail
import Tweet
# db packages
from tinydb import TinyDB, Query
import time
# data/ML packages
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import numpy as np

# constants
DATABASE_PATH = 'data/db.json'
TWEETS_TABLE = 'tweets'
ACCOUNTS_TABLE = 'accounts'
TWEET_URL_PATTERN = 'twitter.com/{handle}/status/{id}'
SECONDS_PER_DAY = 86400
MAX_KEYWORDS = 1000
CLUSTER_COLORS = ['blue', 'orange', 'green','red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
CUSTOM_STOP_WORDS = {'rt'}

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
        if res is not None and 'data' in res.keys():
            # add tweets to dict
            tweets['tweets'].append({
                'handle': handle,
                'tweets': [{'id': entry['id'], 'text': entry['text']} for entry in res['data']]
            })
    # insert new entry into tweets table
    db.table(TWEETS_TABLE).insert(tweets)

# Returns true if old timestamp is from > 24 hours ago, false otherwise
def timestampExpired(old, now=time.time()):
    return (now - old) > SECONDS_PER_DAY

# Sanitizes text by removing special unicode and lowering case
def sanitize(text):
    text = text.lower()
    # remove weird unicode characters
    text = text.encode('ascii', 'ignore').decode("utf-8")
    # remove non alpha tokens and custom stop words
    text = text.split()
    text = list(filter(lambda token: token.isalpha() and token not in CUSTOM_STOP_WORDS, text))
    return " ".join(text)

# Reads most recent tweets from the database and returns them as a list
def parseTweets(db):
    tweets_table = db.table(TWEETS_TABLE)
    tweets_table = tweets_table.get(doc_id=len(tweets_table))
    if 'tweets' not in tweets_table.keys():
        return None
    tweets_table = tweets_table['tweets']
    tweets = []
    for entry in tweets_table:
        handle = entry['handle']
        tweets += [Tweet.Tweet(handle,
                    sanitize(tweet['text']),
                    tweet['id']) for tweet in entry['tweets']]
    return tweets

# Extracts top keywords from the dataset
def extractKeywords(dataset, max_keywords=MAX_KEYWORDS):
    # compile list of all tweet content
    corpus = [tweet.content for tweet in dataset]
    # vectorize dataset and identify keywords
    vectorizer = CountVectorizer(max_df=0.85, stop_words='english', max_features=max_keywords)
    vectorizer.fit_transform(corpus)
    return vectorizer.get_feature_names()

def labelClusters():
    pass

def plotClusters():
    pass

def filterClusters(n=4):
    pass

def draftEmail():
    pass


if __name__ == "__main__":
    # Init
    twitter = Twitter.Twitter()
    gmail = Gmail.Gmail()
    db = TinyDB(DATABASE_PATH)

    # Fetch tweets from last 24 hours
    fetchLatestTweets(twitter, db)

    # Read in tweets as List[Tweet]
    dataset = parseTweets(db)

    # Extract keywords
    keywords = extractKeywords(dataset)

    # Generate email

    # Send email
