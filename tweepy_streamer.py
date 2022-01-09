from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import Cursor
from tweepy import API
from textblob import TextBlob
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import twitter_credentials

class TwitterClient():
    def __init__(self,twitter_user=None):
        #properly authenticate to communicate with the twitter api
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)
        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    #get the tweets in timeline of the authenticated user
    def get_user_timeline_tweets(self,num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline,id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets
    
    def get_friend_list(self,num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.get_friends,id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list
    
    def get_home_timeline_tweets(self,num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline,id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets

class TwitterAuthenticator():
    def authenticate_twitter_app(self):
        auth = OAuthHandler(consumer_key=twitter_credentials.CONSUMER_KEY,consumer_secret=twitter_credentials.CONSUMER_KEY_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN,twitter_credentials.ACCESS_TOKEN_SECRET) 
        return auth


class TwitterStreamer():
    """
        Streaming and processing live tweets
    """
    def __init__(self):
        self.twitter_authenticator = TwitterAuthenticator()

    def stream_tweets(self,fetched_tweets_filename,hash_tag_list):

        #handles authentication and connection to the twitter streaming api
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_authenticator.authenticate_twitter_app()
        stream = Stream(auth,listener)
        stream.filter(track=hash_tag_list)


#print the received tweets to stdout
class TwitterListener(StreamListener):

    def __init__(self,fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self,raw_data):
        try:
            print(raw_data)
            with open(self.fetched_tweets_filename,'a') as tf:
                tf.write(raw_data)
        except BaseException as e:
            print("Error : " % str(e))
        return True

    def on_error(self,errStatus):
        if(errStatus == 420):
            #returning false on data method in case rate limit is exceeded
            return False
        print(errStatus)


class TweetAnalyzer():
    """
    Functionality for analysing and categorising content from tweets
    """
    def clean_tweet(self,tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        
        #positive
        if analysis.sentiment.polarity > 0:
            return 1
        
        #neutral tweet
        elif analysis.sentiment.polarity == 0:
            return 0
        
        #Negative
        else:
            return -1

    def tweets_to_data_frame(self,tweets):

        df = pd.DataFrame(data=[tweet.text for tweet in tweets],columns=['tweets'])
        df['id'] = np.array([tweet.id for tweet in tweets])
        df['len'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        df['source'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])
        
        return df



if __name__ == "__main__":
    
    twitter_client = TwitterClient()
    tweet_analyzer = TweetAnalyzer()

    api = twitter_client.get_twitter_client_api()
    user_name = input("Enter twitter handle name : ").split(' ')[0]

    tweets = api.user_timeline(screen_name="@"+user_name,count=100)
    df = tweet_analyzer.tweets_to_data_frame(tweets)
    df['sentiment'] = np.array([tweet_analyzer.analyze_sentiment(tweet)for tweet in df['tweets']])
    '''
        Visualisation and Analysis
    '''

    #average length of all the tweets
    print("Average length of the tweets : ",np.mean(df['len']))

    #max number of likes for the most liked tweet
    print("Number of likes for the most liked tweet" ,np.max(df['likes']))    

    #max number of retweets for the most retweet
    print("Number of retweets for the most retweeted tweet" ,np.max(df['retweets']))

    print(df.head(20))

    #Time series
    time_likes = pd.Series(data=df['likes'].values, index=df['date'])
    time_likes.plot(figsize=(16,4),label="likes",legend=True)
    
    time_retweets = pd.Series(data=df['retweets'].values, index=df['date'])
    time_retweets.plot(figsize=(16,4),label="retweets",legend=True)
    
    plt.show()
    