"""
X/Twitter Account Monitor for RSSdeck-MCP

Monitors X accounts via manual tweet URL fetching.
Since X API is paid, we use FxTwitter for individual tweets.

Usage:
  - Add tweet URLs to monitor in urls.txt
  - Run: python x_monitor.py
  - Or call fetch_tweet_url("https://x.com/handle/status/123") directly
"""

import json
import urllib.request
import urllib.error
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Tweet:
    id: str
    author: str
    handle: str
    content: str
    created_at: str
    likes: int
    retweets: int
    views: int
    url: str

# URLs to monitor (add any X URLs here)
MONITOR_URLS = [
    "https://x.com/karpathy/status/1896866532301783062",  # Claws
    "https://x.com/simonwillison/status/1896861234567890",
]

def fetch_tweet(url: str) -> Optional[Tweet]:
    """Fetch a single tweet using FxTwitter API"""
    try:
        # Extract handle and ID from URL
        parts = url.split("/")
        handle = parts[-2] if len(parts) >= 2 else ""
        tweet_id = parts[-1] if parts else ""
        
        api_url = f"https://api.fxtwitter.com/{handle}/status/{tweet_id}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        if data.get("code") != 200:
            print(f"Error: {data.get('message', 'Unknown')}")
            return None
        
        tweet_data = data.get("tweet", {})
        author_data = tweet_data.get("author", {})
        
        return Tweet(
            id=str(tweet_data.get("id", "")),
            author=author_data.get("name", ""),
            handle=author_data.get("screen_name", ""),
            content=tweet_data.get("text", ""),
            created_at=tweet_data.get("created_at", ""),
            likes=tweet_data.get("like_count", 0),
            retweets=tweet_data.get("retweet_count", 0),
            views=tweet_data.get("views", {}).get("count", 0) if "views" in tweet_data else 0,
            url=url,
        )
        
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def fetch_all(urls: List[str]) -> List[Tweet]:
    """Fetch multiple tweets"""
    tweets = []
    for url in urls:
        tweet = fetch_tweet(url)
        if tweet:
            tweets.append(tweet)
    return tweets

def summarize(tweets: List[Tweet]) -> str:
    """Generate token-efficient summary"""
    if not tweets:
        return "No tweets to summarize"
    
    result = f"X/Twitter Monitor ({len(tweets)} tweets):\n\n"
    for i, t in enumerate(tweets, 1):
        content = t.content[:100] + "..." if len(t.content) > 100 else t.content
        result += f"{i}. @{t.handle}: {content}\n"
        result += f"   ❤️{t.likes} 🔁{t.retweets} 👁️{t.views}\n\n"
    
    return result

# Test
if __name__ == "__main__":
    print("=== X Account Monitor ===\n")
    
    # Test with a known tweet
    test_url = "https://x.com/karpathy/status/1896866532301783062"
    print(f"Fetching: {test_url}")
    
    tweet = fetch_tweet(test_url)
    if tweet:
        print(f"\n@{tweet.handle}: {tweet.content[:150]}...")
        print(f"Likes: {tweet.likes}, Retweets: {tweet.retweets}, Views: {tweet.views}")
    else:
        print("Failed to fetch tweet")
