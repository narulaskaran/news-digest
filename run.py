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
SECONDS_PER_DAY = 86400
MAX_KEYWORDS = 1000
MIN_CLUSTERS = 100
MAX_CLUSTERS = 101
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

# Takes a nested list and collapses it by one degree
def collapseNestedList(nested):
    flattened = []
    for element in nested:
        flattened += element
    return flattened
    
def clusterTweets(keywords, matrix, dataset, num_clusters=8):
    # cluster and label each vector
    km = KMeans(n_clusters=num_clusters, max_iter=1000).fit(matrix)
    labels = km.labels_
    # unwind one layer of dataset
    tweets = collapseNestedList(dataset)
    # make keywords index-able
    keywords = np.mat(keywords).T
    # compile list of keywords + tweets for each cluster
    clustered_keywords = [{} for i in range(num_clusters)]
    clustered_tweets = [[] for i in range(num_clusters)]
    for tweet_idx in range(len(labels)):
        cluster_idx = labels[tweet_idx]
        words = keywords[matrix[tweet_idx].T.todense() == True]
        for word in words.flatten().tolist()[0]:
            if word not in clustered_keywords[cluster_idx]:
                clustered_keywords[cluster_idx][word] = 0
            clustered_keywords[cluster_idx][word] += 1
        clustered_tweets[cluster_idx].append(tweets[tweet_idx])
    # choose top 3 keywords per cluster
    for cluster_idx in range(len(clustered_keywords)):
        lib = clustered_keywords[cluster_idx]
        lib = sorted(lib, key=lambda k: lib[k])[:5]
        clustered_keywords[cluster_idx] = set(lib)
    return clustered_keywords, clustered_tweets, silhouette_score(matrix, km.labels_, metric='euclidean'), labels

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

    # Cluster tweets with different numbers of clusters to determine optimal clustering
    num_clusters_to_results = {}
    for num_clusters in range(MIN_CLUSTERS, MAX_CLUSTERS):
        num_clusters_to_results[num_clusters] = clusterTweets(keywords, matrix, dataset, num_clusters=num_clusters)

    # Choose optimal clustering (one with highest silhouette score)
    # There is a chance that results will vary upon rerunning the program
    #   as K-Means can get stuck in local minima
    optimal_score = -np.infty
    optimal_num_clusters = MIN_CLUSTERS
    clustered_keywords = []
    clustered_tweets = []
    optimal_labels = []
    plot_data = {
                'num_clusters': [],
                'silhouette_scores': [],
                'labels': []
                }
    for num_clusters in num_clusters_to_results.keys():
        words, tweets, score, labels = num_clusters_to_results.get(num_clusters)
        # store data for plotting
        plot_data['num_clusters'].append(num_clusters)
        plot_data['silhouette_scores'].append(score)
        plot_data['labels'].append(labels)
        #check for optimal score
        if score > optimal_score:
            optimal_num_clusters = num_clusters
            clustered_keywords = words
            clustered_tweets = tweets
            optimal_score = score
            optimal_labels = labels

    # Merge clusters with common keywords
    merged_keywords = [set() for x in clustered_keywords]
    for word_set in clustered_keywords:
        for cluster_idx in range(len(merged_keywords)):
            merge_set = merged_keywords[cluster_idx]
            if len(merge_set) == 0 or len(merge_set.intersection(word_set)) > 0:
                merged_keywords[cluster_idx] = merge_set.union(word_set)
                break
    merged_keywords = list(filter(lambda x: len(x) > 0, merged_keywords))

    # Inverse lookup from keyword to cluster
    lookup = {}
    for cluster_idx in range(len(merged_keywords)):
        for word in merged_keywords[cluster_idx]:
            lookup[word] = cluster_idx
    
    # Re-classify tweets
    num_clusters = len(merged_keywords)
    tweets = collapseNestedList(dataset)
    cluster_counts = [0 for i in range(num_clusters)]
    for tweet_idx in range(len(tweets)):
        tweet = tweets[tweet_idx]
        cluster_votes = {}
        for i in range(num_clusters):
            cluster_votes[i] = 0
        for word in tweet.content.split():
            if word in lookup.keys():
                cluster_votes[lookup[word]] += 1
        # top voted cluster
        cluster_assignment = 0
        max_votes = cluster_votes[cluster_assignment]
        for k in cluster_votes.keys():
            v = cluster_votes[k]
            if v > max_votes:
                cluster_assignment = k
                max_votes = v
        # update cluster labels for all tweets
        labels[tweet_idx] = cluster_assignment
        cluster_counts[cluster_assignment] += 1

    # Filter top 6 clusters
    cluster_counts = [(i, cluster_counts[i]) for i in range(len(cluster_counts))]
    cluster_counts = sorted(cluster_counts, key=lambda wrapper: wrapper[1])
    cluster_counts.reverse()
    clusters = [x[0] for x in cluster_counts[:6]]
        
    # Plot silhouette scores 
    plt.plot(plot_data['num_clusters'], plot_data['silhouette_scores'])
    plt.title('Silhouette Score vs Number of Clusters')
    plt.savefig('figures/silhouette_scores.png')
    plt.figure()

    # Reduce dataset to 2 axes via PCA
    scaled_dataset = PCA(3).fit_transform(matrix.todense())

    # Plot clusters
    for cluster_idx in range(len(clusters)):
        cluster_points = scaled_dataset[labels == clusters[cluster_idx]]
        plt.scatter(cluster_points[:,0], cluster_points[:,1], color=CLUSTER_COLORS[cluster_idx])
    plt.savefig('figures/{}_keyword_clustering.png'.format(MAX_KEYWORDS))
    plt.figure()

    # Print out cluster keywords for sanity check
    for cluster in clusters:
        print('\n############ CLUSTER {} ############'.format(cluster))
        print(merged_keywords[cluster])

    # Generate email

    # Send email
