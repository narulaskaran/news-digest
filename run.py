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
import numpy as np

# constants
DATABASE_PATH = 'data/db.json'
TWEETS_TABLE = 'tweets'
ACCOUNTS_TABLE = 'accounts'
SECONDS_PER_DAY = 86400
MAX_KEYWORDS = 500
MIN_CLUSTERS = 3
MAX_CLUSTERS = 15

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

def extractKeywords(dataset):
    # compile list of all tweet content
    corpus = []
    for user_tweets in dataset:
        for tweet in user_tweets:
            # remove non alpha tokens
            text = tweet.content.split()
            text = list(filter(lambda token: token.isalpha(), text))
            corpus.append(" ".join(text))
    # vectorize dataset and return features
    vectorizer = CountVectorizer(max_df=0.85, stop_words='english', max_features=MAX_KEYWORDS)
    feature_matrix = vectorizer.fit_transform(corpus)
    return vectorizer.get_feature_names(), feature_matrix
    
def clusterTweets(keywords, matrix, dataset, num_clusters=8):
    # cluster and label each vector
    km = KMeans(n_clusters=num_clusters).fit(matrix)
    labels = km.labels_
    # unwind one layer of dataset
    tweets = []
    for user in dataset:
        tweets += user
    # make keywords index-able
    keywords = np.mat(keywords).T
    # compile list of keywords + tweets for each cluster
    clustered_keywords = [set() for i in range(num_clusters)]
    clustered_tweets = [[] for i in range(num_clusters)]
    for tweet_idx in range(len(labels)):
        cluster_idx = labels[tweet_idx]
        words = keywords[matrix[tweet_idx].T.todense() == True]
        for word in words.flatten().tolist()[0]:
            clustered_keywords[cluster_idx].add(word)
        clustered_tweets[cluster_idx].append(tweets[tweet_idx])
    return clustered_keywords, clustered_tweets, silhouette_score(matrix, km.labels_, metric='euclidean')

def calculateClusteringError():
    pass

def labelClusters():
    pass

def plotClusters():
    pass

def filterClusters(n=4):
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
    keywords, matrix = extractKeywords(dataset)

    # Cluster tweets, multiple times to determine optimal number of clusters
    num_clusters_to_results = {}
    for num_clusters in range(MIN_CLUSTERS, MAX_CLUSTERS):
        num_clusters_to_results[num_clusters] = clusterTweets(keywords, matrix, dataset, num_clusters=num_clusters)

    # Choose optimal clustering (one with highest silhouette score)
    optimal_score = 0
    optimal_num_clusters = MIN_CLUSTERS
    clustered_keywords = []
    clustered_tweets = []
    for num_clusters in num_clusters_to_results.keys():
        words, tweets, score = num_clusters_to_results.get(num_clusters)
        if score > optimal_score:
            optimal_num_clusters = num_clusters
            clustered_keywords = words
            clustered_tweets = tweets
            optimal_score = score


    # Label clusters
    labelClusters()

    # Score clusters

    # Send email
