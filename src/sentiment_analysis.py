"""
Sentiment analysis module for cryptocurrency trading.
This module analyzes sentiment from X.com (formerly Twitter) posts
to help inform trading decisions.
"""

import json
import re
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import tweepy
from textblob import TextBlob
import nltk
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class SentimentAnalyzer:
    """
    A class to analyze sentiment from X.com (formerly Twitter) for cryptocurrencies.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the sentiment analyzer with configuration.
        
        Args:
            config_path: Path to the configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Extract sentiment analysis parameters from config
        self.sentiment_config = self.config["sentiment_analysis"]
        
        # Initialize parameters
        self.min_tweets = self.sentiment_config["min_tweets_for_analysis"]
        self.sentiment_threshold_positive = self.sentiment_config["sentiment_threshold_positive"]
        self.sentiment_threshold_negative = self.sentiment_config["sentiment_threshold_negative"]
        self.influencer_weight = self.sentiment_config["influencer_weight_multiplier"]
        self.keywords = self.sentiment_config["keywords"]
        self.influencers = self.sentiment_config["influencers"]
        
        # Initialize Twitter API client
        self._initialize_twitter_client()
    
    def _initialize_twitter_client(self):
        """Initialize the Twitter API client using credentials from config or env vars."""
        # Get credentials from environment variables or config
        api_key = os.getenv("TWITTER_API_KEY", self.config["twitter"]["api_key"])
        api_secret = os.getenv("TWITTER_API_SECRET", self.config["twitter"]["api_secret"])
        access_token = os.getenv("TWITTER_ACCESS_TOKEN", self.config["twitter"]["access_token"])
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", self.config["twitter"]["access_token_secret"])
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN", self.config["twitter"]["bearer_token"])
        
        # Initialize Twitter client
        try:
            # For v2 API (preferred)
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            logger.info("Initialized Twitter API v2 client")
            self.api_version = "v2"
        except Exception as e:
            logger.warning(f"Failed to initialize Twitter API v2 client: {str(e)}")
            logger.warning("Falling back to v1.1 API")
            
            # For v1.1 API (fallback)
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_token_secret
            )
            self.client = tweepy.API(auth)
            self.api_version = "v1.1"
            logger.info("Initialized Twitter API v1.1 client")
    
    def _clean_tweet(self, tweet: str) -> str:
        """
        Clean the tweet text by removing links, special characters, etc.
        
        Args:
            tweet: The raw tweet text
            
        Returns:
            str: Cleaned tweet text
        """
        # Remove URLs
        tweet = re.sub(r'http\S+', '', tweet)
        
        # Remove mentions (@username)
        tweet = re.sub(r'@\w+', '', tweet)
        
        # Remove hashtags
        tweet = re.sub(r'#\w+', '', tweet)
        
        # Remove non-alphanumeric characters
        tweet = re.sub(r'[^\w\s]', '', tweet)
        
        # Remove extra whitespace
        tweet = re.sub(r'\s+', ' ', tweet).strip()
        
        return tweet
    
    def _get_tweet_sentiment(self, tweet: str) -> Tuple[float, str]:
        """
        Get the sentiment score and label for a tweet.
        
        Args:
            tweet: The tweet text
            
        Returns:
            Tuple[float, str]: Sentiment score (-1 to 1) and label (positive, negative, neutral)
        """
        # Clean the tweet
        cleaned_tweet = self._clean_tweet(tweet)
        
        # Skip empty tweets
        if not cleaned_tweet:
            return 0.0, "neutral"
        
        # Analyze sentiment using TextBlob
        analysis = TextBlob(cleaned_tweet)
        
        # Get polarity score (-1 to 1)
        polarity = analysis.sentiment.polarity
        
        # Determine sentiment label
        if polarity > self.sentiment_threshold_positive:
            sentiment = "positive"
        elif polarity < self.sentiment_threshold_negative:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return polarity, sentiment
    
    def _search_tweets_v2(self, query: str, max_results: int = 100, 
                         days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Search for tweets using Twitter API v2.
        
        Args:
            query: The search query
            max_results: Maximum number of tweets to retrieve
            days_back: Number of days to look back
            
        Returns:
            List[Dict]: List of tweet data
        """
        # Calculate start time
        start_time = datetime.utcnow() - timedelta(days=days_back)
        
        try:
            # Search tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username', 'name', 'public_metrics'],
                expansions=['author_id'],
                start_time=start_time
            )
            
            if not response.data:
                logger.warning(f"No tweets found for query: {query}")
                return []
            
            # Create a dictionary to map user IDs to user data
            users = {user.id: user for user in response.includes['users']} if 'users' in response.includes else {}
            
            # Process tweets
            tweets = []
            for tweet in response.data:
                user = users.get(tweet.author_id, None)
                
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.public_metrics['retweet_count'],
                    'like_count': tweet.public_metrics['like_count'],
                    'reply_count': tweet.public_metrics['reply_count'],
                    'author_id': tweet.author_id,
                }
                
                if user:
                    tweet_data.update({
                        'username': user.username,
                        'followers_count': user.public_metrics['followers_count'],
                        'is_influencer': user.username in self.influencers
                    })
                
                tweets.append(tweet_data)
            
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching tweets with v2 API: {str(e)}")
            return []
    
    def _search_tweets_v1(self, query: str, max_results: int = 100, 
                         days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Search for tweets using Twitter API v1.1 (fallback).
        
        Args:
            query: The search query
            max_results: Maximum number of tweets to retrieve
            days_back: Number of days to look back
            
        Returns:
            List[Dict]: List of tweet data
        """
        try:
            # Search tweets
            search_results = tweepy.Cursor(
                self.client.search_tweets,
                q=query,
                lang="en",
                result_type="recent",
                count=100,
                tweet_mode="extended"
            ).items(max_results)
            
            # Process tweets
            tweets = []
            for tweet in search_results:
                # Skip retweets
                if hasattr(tweet, 'retweeted_status'):
                    continue
                
                # Get tweet text
                if hasattr(tweet, 'full_text'):
                    text = tweet.full_text
                else:
                    text = tweet.text
                
                tweet_data = {
                    'id': tweet.id,
                    'text': text,
                    'created_at': tweet.created_at,
                    'retweet_count': tweet.retweet_count,
                    'like_count': tweet.favorite_count,
                    'reply_count': 0,  # Not available in v1.1
                    'author_id': tweet.user.id,
                    'username': tweet.user.screen_name,
                    'followers_count': tweet.user.followers_count,
                    'is_influencer': tweet.user.screen_name in self.influencers
                }
                
                tweets.append(tweet_data)
            
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching tweets with v1.1 API: {str(e)}")
            return []
    
    def search_tweets(self, query: str, max_results: int = 100, 
                     days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Search for tweets using the appropriate Twitter API version.
        
        Args:
            query: The search query
            max_results: Maximum number of tweets to retrieve
            days_back: Number of days to look back
            
        Returns:
            List[Dict]: List of tweet data
        """
        if self.api_version == "v2":
            return self._search_tweets_v2(query, max_results, days_back)
        else:
            return self._search_tweets_v1(query, max_results, days_back)
    
    def analyze_sentiment(self, token_symbol: str, additional_keywords: List[str] = None) -> Dict[str, Any]:
        """
        Analyze sentiment for a specific cryptocurrency token.
        
        Args:
            token_symbol: The token symbol (e.g., BTC, ETH)
            additional_keywords: Additional keywords to include in the search
            
        Returns:
            Dict: Sentiment analysis results
        """
        # Prepare search query
        search_terms = [token_symbol]
        
        # Add token name variations
        if token_symbol.lower() == "btc":
            search_terms.extend(["bitcoin", "BTC"])
        elif token_symbol.lower() == "eth":
            search_terms.extend(["ethereum", "ETH"])
        
        # Add additional keywords if provided
        if additional_keywords:
            search_terms.extend(additional_keywords)
        
        # Add general crypto keywords
        search_terms.extend(self.keywords)
        
        # Build query string
        query = " OR ".join([f'"{term}"' for term in search_terms])
        
        # Search tweets
        tweets = self.search_tweets(query, max_results=200, days_back=2)
        
        if not tweets:
            logger.warning(f"No tweets found for {token_symbol}")
            return {
                "token": token_symbol,
                "sentiment_score": 0,
                "sentiment": "neutral",
                "tweet_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "influencer_sentiment": "neutral",
                "recent_tweets": [],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Analyze sentiment for each tweet
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        influencer_scores = []
        
        for tweet in tweets:
            # Get sentiment
            score, sentiment = self._get_tweet_sentiment(tweet["text"])
            
            # Add sentiment data to tweet
            tweet["sentiment_score"] = score
            tweet["sentiment"] = sentiment
            
            # Update counts
            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1
            
            # Apply weighting based on engagement and followers
            weight = 1.0
            
            # Engagement weight (likes, retweets, replies)
            engagement = tweet.get("like_count", 0) + tweet.get("retweet_count", 0) + tweet.get("reply_count", 0)
            if engagement > 100:
                weight *= 1.5
            elif engagement > 50:
                weight *= 1.3
            elif engagement > 10:
                weight *= 1.1
            
            # Follower weight
            followers = tweet.get("followers_count", 0)
            if followers > 100000:
                weight *= 1.5
            elif followers > 10000:
                weight *= 1.3
            elif followers > 1000:
                weight *= 1.1
            
            # Influencer weight
            if tweet.get("is_influencer", False):
                weight *= self.influencer_weight
                influencer_scores.append(score * weight)
            
            # Add weighted score
            sentiment_scores.append(score * weight)
        
        # Calculate overall sentiment
        if sentiment_scores:
            overall_score = sum(sentiment_scores) / len(sentiment_scores)
        else:
            overall_score = 0
        
        # Determine overall sentiment label
        if overall_score > self.sentiment_threshold_positive:
            overall_sentiment = "positive"
        elif overall_score < self.sentiment_threshold_negative:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        # Calculate influencer sentiment
        if influencer_scores:
            influencer_score = sum(influencer_scores) / len(influencer_scores)
            
            if influencer_score > self.sentiment_threshold_positive:
                influencer_sentiment = "positive"
            elif influencer_score < self.sentiment_threshold_negative:
                influencer_sentiment = "negative"
            else:
                influencer_sentiment = "neutral"
        else:
            influencer_sentiment = "neutral"
        
        # Sort tweets by engagement for recent tweets sample
        sorted_tweets = sorted(
            tweets, 
            key=lambda x: x.get("like_count", 0) + x.get("retweet_count", 0), 
            reverse=True
        )
        
        # Get top 10 tweets
        recent_tweets = sorted_tweets[:10]
        
        # Return results
        return {
            "token": token_symbol,
            "sentiment_score": overall_score,
            "sentiment": overall_sentiment,
            "tweet_count": len(tweets),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": (positive_count / len(tweets)) * 100 if tweets else 0,
            "negative_percentage": (negative_count / len(tweets)) * 100 if tweets else 0,
            "neutral_percentage": (neutral_count / len(tweets)) * 100 if tweets else 0,
            "influencer_sentiment": influencer_sentiment,
            "recent_tweets": recent_tweets,
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    # Example usage
    analyzer = SentimentAnalyzer("../config/config.json")
    
    # Analyze sentiment for Bitcoin
    btc_sentiment = analyzer.analyze_sentiment("BTC")
    
    # Print results
    print(json.dumps(btc_sentiment, indent=2, default=str))
