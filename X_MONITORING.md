# X/Twitter Monitor for RSSdeck-MCP

## Status: Setup Complete (Manual Mode)

Due to X's API restrictions, keyword search requires a paid API. Here's how we monitor X:

## Current Options:

### 1. Manual Tweet URLs
Add tweet URLs to `x_urls.txt` (one per line):
```
https://x.com/karpathy/status/1234567890
https://x.com/simonwillison/status/0987654321
```

Then run: `python x_monitor.py` to fetch and summarize.

### 2. x-tweet-fetcher Skill
Use the installed skill to fetch any tweet:
```bash
cd ~/.openclaw/workspace/skills/x-tweet-fetcher
./scripts/fetch_tweet.py --url "https://x.com/karpathy/status/XXXX"
```

### 3. Future: X API
When you have X API access, we can add:
- Keyword search
- Account timeline monitoring
- Real-time alerts

## What's Working Now:

- RSS feeds: 30 sources, 149+ articles
- MCP: Token-efficient summaries
- Daily intelligence to Notion

## To Add X Monitoring:

Just give me tweet URLs you, and I'll add want tracked them to the monitor. Or get X API keys for automatic monitoring.

---
*This is a placeholder until we have X API access or you provide specific tweet URLs to track.*
