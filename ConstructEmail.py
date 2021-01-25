from datetime import date

class ConstructEmail:
    def __init__(self, keywordsByCluster, tweetsByCluster):
        tweetsByCluster = [pair[1] for pair in tweetsByCluster]
        if len(keywordsByCluster) != len(tweetsByCluster):
            raise ValueError('len(keywordsByCluster) should equal len(tweetsByCluster)')
        self.html = """\
                    <html>
                        <head>
                            <style>
                                blockquote.twitter-tweet {{
                                    display: inline-block;
                                    font-family: "Helvetica Neue", Roboto, "Segoe UI", Calibri, sans-serif;
                                    font-size: 12px;
                                    font-weight: bold;
                                    line-height: 16px;
                                    border-color: #eee #ddd #bbb;
                                    background-color: rgba(29, 161, 242, 0.1);
                                    border-radius: 5px;
                                    border-style: solid;
                                    border-width: 1px;
                                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
                                    margin: 10px 5px;
                                    padding: 0 16px 16px 16px;
                                    max-width: 468px;
                                }}

                                blockquote.twitter-tweet p {{
                                    font-size: 16px;
                                    font-weight: normal;
                                    line-height: 20px;
                                }}

                                blockquote.twitter-tweet a {{
                                    color: inherit;
                                    font-weight: normal;
                                    text-decoration: none;
                                    outline: 0 none;
                                }}

                                blockquote.twitter-tweet a:hover,
                                blockquote.twitter-tweet a:focus {{
                                    text-decoration: underline;
                                }}

                                blockquote.twitter-tweet h3 {{
                                    color: blue;
                                }}
                            </style>
                        </head>
                        <body>
                            <h1>
                                Your <a href='twitter.com'>Twitter</a> news digest for {date}.
                            </h1>
                            <p>
                                Generated using tweet data from the last 24 hours.
                                Find the list of accounts I pull from <a href='https://github.com/narulaskaran/news-digest/blob/main/config/config.json'>here.</a>
                            </p>
                            <h1>
                                News topics from yesterday
                            </h1>
                            {topics}
                        </body>
                    </html>
                    """
        self.url_pattern = 'twitter.com/{handle}/status/{id}'
        # format topic fragments
        topicFragments = []
        for idx in range(len(keywordsByCluster)):
            topicFragments.append("""\
                                    <h2>
                                        {keywords}
                                    </h2>
                                    <details style='display:flex'>
                                        <summary></summary>
                                        {tweets}
                                    </details>
                                """.format(keywords=', '.join(keywordsByCluster[idx]), tweets=self.serializeTweets(keywordsByCluster[idx], tweetsByCluster[idx])))
        # insert fragments into template
        self.html = self.html.format(date=date.today(), topics=''.join(topicFragments))
        self.html = self.html.replace('\\n', '')
    
    def serializeTweets(self, keywords, tweets):
        template = """\
            <blockquote class="twitter-tweet">
                <a href={url}>
                    <h3>@{handle}</h3>
                    <p>{content}</p>
                </a>
            </blockquote>
        """
        tweets = self.chooseTopTweets(keywords, tweets)
        # serialize each tweet and concatenate 
        serializedTweets = [template.format(url=(self.url_pattern.format(handle=tweet.handle, id=tweet.id)), handle=tweet.handle, content=tweet.content) for tweet in tweets]
        return "".join(serializedTweets)

    def chooseTopTweets(self, keywords, tweets, n=5):
        tweet_scores = [0 for tweet in tweets]
        for idx in range(len(tweets)):
            words = tweets[idx].content.split()
            for word in words:
                tweet_scores[idx] += 1 if word in set(keywords) else 0
        tweets = zip(tweet_scores, tweets)
        tweets = sorted(tweets, key=lambda x: x[0], reverse=True)[:n]
        tweets = [tweet[1] for tweet in tweets]
        return tweets



    def getEmailBody(self):
        return self.html
