# Personal packages
import Twitter
import Gmail
import Tweet
# DB packages
from tinydb import TinyDB, Query
import time
# Data/ML packages
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
from gensim.models import Word2Vec
# System packages
import multiprocessing

# Constants
DATABASE_PATH = 'data/db.json'
TWEETS_TABLE = 'tweets'
ACCOUNTS_TABLE = 'accounts'
TWEET_URL_PATTERN = 'twitter.com/{handle}/status/{id}'
SECONDS_PER_DAY = 86400
MAX_KEYWORDS = 1000
NUM_MATCHING_KEYWORDS_PER_GROUP = 3
NUM_TOPICS_TO_SELECT = 4
NUM_KEYWORDS_PER_GROUP = 5
NUM_CORES = multiprocessing.cpu_count()
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

# Trains W2V model from tweet dataset
def trainModel(dataset):
    corpus = [tweet.content.split() for tweet in dataset]
    w2v_model = Word2Vec(min_count=20,
                     window=2,
                     size=300,
                     sample=6e-5, 
                     alpha=0.03, 
                     min_alpha=0.0007, 
                     negative=20,
                     workers=NUM_CORES-1)
    w2v_model.build_vocab(corpus, progress_per=1000)
    w2v_model.train(corpus, total_examples=w2v_model.corpus_count, epochs=500, report_delay=1)
    return w2v_model

# Creates a weighted simiarlity graph based on keywords and w2v model
def genSemanticGraph(model, keywords):
    # filter out keywords not in the vocabulary
    keywords = list(filter(lambda word: model.wv.__contains__(word), keywords))
    # gen graph
    graph = {}
    for src in keywords:
        graph[src] = {}
        for dest in keywords:
            if src != dest:
                graph[src][dest] = model.wv.similarity(src, dest)
    # sort keys for each source node by weight
    for key in graph.keys():
        children = graph[key]
        graph[key] = [(key, children[key]) for key in sorted(children, key=lambda k: children.get(k), reverse=True)]
    return graph

# Clusters keywords into related groups
def determineTopics(graph):
    # pick out top neighbors for all keywords in the graph
    # {keyword --> set{related keywords}}
    groupings = {}
    for keyword in graph:
        neighbors = set()
        for neighbor in graph[keyword][:6]:
            neighbors.add(neighbor[0])
        groupings[keyword] = neighbors
    # merge groups if they have 3 or more overlapping keywords
    clusters = []
    for keyword in groupings:
        group = groupings[keyword]
        merged = False
        for cluster in clusters:
            if len(group.intersection(cluster)) >= NUM_MATCHING_KEYWORDS_PER_GROUP:
                for x in group:
                    cluster.add(x)
                merged = True
                break
        if not merged:
            clusters.append(group)
    return clusters

# Sorts tweets into clusters
def categorizeTweets(clusters, dataset):
    # for each tweet, count how many keywords it matches per cluster
    # assign the tweet to the top cluster
    clusteredTweets = [[] for cluster in clusters]
    for tweet in dataset:
        scores = [0 for i in range(len(clusters))]
        text = tweet.content
        for word in text.split():
            for cluster_idx in range(len(clusters)):
                scores[cluster_idx] += 1 if word in clusters[cluster_idx] else 0
        max_cluster_idx = np.argmax(scores)
        clusteredTweets[max_cluster_idx].append(tweet)
    return clusteredTweets

def filterClusters(clusters, clusteredTweets, n=NUM_TOPICS_TO_SELECT):
    clusterCounts = [(idx, len(clusteredTweets[idx])) for idx in range(len(clusteredTweets))]
    topicIndices = [el[0] for el in sorted(clusterCounts, key=lambda x: x[1], reverse=True)[:n]]
    filteredClusters = []
    for idx in topicIndices:
        filteredClusters.append((clusters[idx], clusteredTweets[idx]))
    return filteredClusters

def genTightestNodesPerCluster(model, clusterTopics, n=NUM_KEYWORDS_PER_GROUP):
    topKeywords = []
    for cluster in clusterTopics:
        # score each node
        scores = {}
        for nodeA in cluster:
            score = 0
            for nodeB in cluster:
                if nodeA == nodeB:
                    continue
                score += model.wv.similarity(nodeA, nodeB)
            scores[nodeA] = score
        # choose top n nodes
        topKeywords.append(sorted(sorted(scores, key=lambda k: scores[k], reverse=True)[:n]))
    return topKeywords

def plotClusters():
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

    # Build vocab and train model
    model = trainModel(dataset)

    # Build semantic graph of keyword similarity
    graph = genSemanticGraph(model, keywords)

    # Break tweets up into distinct topics based on keyword relaitonships
    clusters = determineTopics(graph)

    # Categorize tweets into topics
    sortedTweets = categorizeTweets(clusters, dataset)

    # Choose top n clusters of tweets
    # Type  --  List[Tuple(Set(), List[Tweet])]
    filteredSortedTweets = filterClusters(clusters, sortedTweets)

    # Determine most important keywords per cluster (for email headings)
    filteredTopics = [pair[0] for pair in filteredSortedTweets]
    filteredTopics = genTightestNodesPerCluster(model, filteredTopics)
    print(filteredTopics)
    
    # Generate email

    # Send email
