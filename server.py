"""
RSSdeck V2 - MCP Server for AI Agents

A token-efficient RSS service designed for AI agents.
"""

import os
import asyncio
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import httpx
import feedparser
from bs4 import BeautifulSoup
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

# Local imports
from rss_db import (
    add_feed, get_all_feeds, store_article, store_articles,
    get_articles, search_articles, get_sentiment_breakdown,
    get_top_sources, generate_rss_report
)

load_dotenv()

# Config
RSSDECK_URL = os.getenv("RSSDECK_URL", "http://localhost:3001")
INTERESTS = [i.strip().lower() for i in os.getenv("INTERESTS", "AI,operations,Malaysia,APAC,business,technology,management").split(",")]

# For backwards compatibility, also check OPML file
RSSDECK_OPML = os.getenv("RSSDECK_OPML", os.path.join(os.path.dirname(__file__), "../rssdeck/feeds/opml/rssdeck-feeds.opml"))

# Default feeds when RSSdeck API not available
DEFAULT_FEEDS = [
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
    {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/"},
]

# In-memory cache
# Default feeds (fallback when RSSdeck API not available)
@dataclass
class Article:
    id: str
    title: str
    link: str
    summary: str
    published: str
    source: str
    content: str = ""
    sentiment: str = "neutral"
    relevance_score: float = 0.0

class ArticleCache:
    def __init__(self):
        self.articles: dict[str, Article] = {}
        self.seen_ids: set[str] = set()
    
    def add(self, article: Article):
        self.articles[article.id] = article
    
    def get_all(self):
        return list(self.articles.values())
    
    def get_new(self, since_hours=24):
        cutoff = datetime.now() - timedelta(hours=since_hours)
        result = []
        for a in self.articles.values():
            try:
                # Try multiple date formats
                published_dt = None
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        published_dt = datetime.strptime(a.published, fmt)
                        break
                    except:
                        continue
                
                if published_dt and published_dt > cutoff:
                    result.append(a)
            except:
                # If date parsing fails, include it anyway
                result.append(a)
        return result
    
    def deduplicate(self):
        """Remove duplicate stories based on title similarity"""
        seen_titles = set()
        unique = []
        for a in self.articles.values():
            title_norm = a.title.lower().strip()
            if title_norm not in seen_titles:
                seen_titles.add(title_norm)
                unique.append(a)
        return unique

cache = ArticleCache()

async def fetch_rss(url: str) -> list[dict]:
    """Fetch and parse RSS feed"""
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        
        articles = []
        for entry in feed.entries[:10]:  # Limit to 10 per feed
            # Generate ID from URL or title
            entry_id = hashlib.md5(entry.link.encode()).hexdigest() if hasattr(entry, 'link') else hashlib.md5(entry.title.encode()).hexdigest()
            
            summary = entry.get("summary", entry.get("description", ""))
            # Clean HTML
            summary = re.sub(r'<[^>]+>', '', summary)[:200]
            
            article = {
                "id": entry_id,
                "title": entry.title,
                "link": entry.link,
                "summary": summary,
                "published": entry.get("published", datetime.now().isoformat()),
                "source": feed.feed.get("title", "Unknown"),
                "content": entry.get("content", [{"value": ""}])[0].value if entry.get("content") else ""
            }
            articles.append(article)
        
        return articles
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def calculate_relevance(title: str, summary: str) -> float:
    """Calculate relevance score based on interests"""
    text = f"{title} {summary}".lower()
    score = 0.0
    for interest in INTERESTS:
        if interest.lower() in text:
            score += 1.0
    return min(score / len(INTERESTS), 1.0)

def extract_sentiment(title: str, summary: str) -> str:
    """Simple sentiment analysis"""
    text = f"{title} {summary}".lower()
    positive = ["up", "growth", "success", "new", "launch", "release", "improve", "best", "win"]
    negative = ["fail", "crash", "bug", "vulnerability", "hack", "down", "lose", "problem", "issue"]
    
    pos_count = sum(1 for p in positive if p in text)
    neg_count = sum(1 for n in negative if n in text)
    
    if pos_count > neg_count:
        return "bullish"
    elif neg_count > pos_count:
        return "bearish"
    return "neutral"

def extract_tldr(article: dict) -> str:
    """Generate TL;DR summary"""
    summary = article.get("summary", "")
    title = article.get("title", "")
    
    # Simple extraction - in production, use LLM
    sentences = summary.split(". ")
    if len(sentences) >= 2:
        tldr = f"{sentences[0]}. {sentences[1][:100]}..."
    else:
        tldr = summary[:150] + "..."
    
    return tldr

def parse_opml_feeds(opml_path: str) -> list[dict]:
    """Parse OPML file and return list of feeds"""
    feeds = []
    try:
        # Read file and remove comments
        with open(opml_path, 'r') as f:
            content = f.read()
        
        # Handle unescaped & in URLs by replacing & with &amp; outside of tags
        # First, find all xmlUrl attributes and escape their & properly
        import re
        content = re.sub(r'(xmlUrl="[^"]*)&(.*?")', r'\1&amp;\2', content)
        
        # Remove XML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        # Remove processing instructions
        content = re.sub(r'<\?.*?\?>', '', content)
        
        root = ET.fromstring(content)
        for outline in root.findall(".//outline"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                # Unescape the &amp; back to & for the URL
                xml_url = xml_url.replace('&amp;', '&')
                feeds.append({
                    "name": outline.get("text", outline.get("title", "Unknown")),
                    "url": xml_url,
                })
    except Exception as e:
        print(f"Error parsing OPML: {e}")
        # Fallback feeds
        feeds = [
            {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
            {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/"},
        ]
    return feeds

async def get_feeds_from_rssdeck() -> list[dict]:
    """Get feeds from RSSdeck via API - for future use when frontend passes feeds"""
    # This would be called by frontend passing feeds directly
    # For now, we use DEFAULT_FEEDS or OPML
    return DEFAULT_FEEDS

async def refresh_cache():
    """Refresh article cache from RSSdeck"""
    # Try to get feeds from OPML first (what we have now)
    feed_list = parse_opml_feeds(RSSDECK_OPML)
    
    # Track feeds in database
    for feed in feed_list:
        add_feed(feed["name"], feed["url"])
    
    for feed in feed_list:
        articles = await fetch_rss(feed["url"])
        
        # Store in database
        store_articles(articles)
        
        for a in articles:
            article = Article(
                id=a["id"],
                title=a["title"],
                link=a["link"],
                summary=a["summary"],
                published=a["published"],
                source=a["source"],
                relevance_score=calculate_relevance(a["title"], a["summary"]),
                sentiment=extract_sentiment(a["title"], a["summary"])
            )
            cache.add(article)

# MCP Server setup
app = Server("rssdeck-v2")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_feeds",
            description="List all configured RSS feeds",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_updates",
            description="Get latest articles with summaries. Returns token-efficient summaries, not full articles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {"type": "number", "default": 24, "description": "Hours to look back"},
                    "interest_filter": {"type": "string", "default": "", "description": "Filter by interest"},
                    "max_results": {"type": "number", "default": 10, "description": "Max articles to return"}
                }
            }
        ),
        Tool(
            name="search",
            description="Search across cached articles",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "number", "default": 5}
                }
            }
        ),
        Tool(
            name="get_summary",
            description="Get detailed summary of a specific article",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {"type": "string", "description": "Article ID"}
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_feeds":
        feed_list = parse_opml_feeds(RSSDECK_OPML)
        return [TextContent(type="text", text=json.dumps({
            "feeds": feed_list,
            "interests": INTERESTS,
            "source": "OPML"
        }))]
    
    elif name == "get_updates":
        await refresh_cache()
        
        hours = arguments.get("hours", 24)
        interest_filter = arguments.get("interest_filter", "")
        max_results = arguments.get("max_results", 10)
        
        # Get new articles
        articles = cache.get_new(hours)
        
        # Deduplicate
        articles = cache.deduplicate()
        
        # Filter by interest
        if interest_filter:
            articles = [a for a in articles if interest_filter.lower() in f"{a.title} {a.summary}".lower()]
        
        # Sort by relevance
        articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit
        articles = articles[:max_results]
        
        results = []
        for a in articles:
            results.append({
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "published": a.published,
                "tldr": generate_tldr({"title": a.title, "summary": a.summary}),
                "sentiment": a.sentiment,
                "relevance": a.relevance_score,
                "url": a.link
            })
        
        return [TextContent(type="text", text=json.dumps({
            "count": len(results),
            "articles": results,
            "token_tip": "These are TL;DR summaries, not full articles. Use get_summary for details."
        }))]
    
    elif name == "search":
        query = arguments.get("query", "").lower()
        max_results = arguments.get("max_results", 5)
        
        results = []
        for a in cache.get_all():
            if query in a.title.lower() or query in a.summary.lower():
                results.append({
                    "id": a.id,
                    "title": a.title,
                    "source": a.source,
                    "tldr": generate_tldr({"title": a.title, "summary": a.summary}),
                    "url": a.link
                })
        
        results = results[:max_results]
        
        return [TextContent(type="text", text=json.dumps({
            "query": query,
            "count": len(results),
            "results": results
        }))]
    
    elif name == "get_summary":
        article_id = arguments.get("article_id", "")
        article = cache.articles.get(article_id)
        
        if not article:
            return [TextContent(type="text", text=json.dumps({"error": "Article not found"}))]
        
        return [TextContent(type="text", text=json.dumps({
            "id": article.id,
            "title": article.title,
            "source": article.source,
            "published": article.published,
            "summary": article.summary,
            "sentiment": article.sentiment,
            "relevance": article.relevance_score,
            "url": article.link,
            "token_note": "Full summary provided. For shorter version, use get_updates."
        }))]
    
    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]

async def background_refresh():
    """Background task to refresh RSS every 2 hours"""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    while True:
        try:
            logger.info("Background: Refreshing RSS feeds...")
            await refresh_cache()
            logger.info("Background: Refresh complete. Sleeping for 2 hours.")
        except Exception as e:
            logger.error(f"Background refresh error: {e}")
        
        await asyncio.sleep(2 * 60 * 60)  # 2 hours

async def main():
    # Start background refresh task
    refresh_task = asyncio.create_task(background_refresh())
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
