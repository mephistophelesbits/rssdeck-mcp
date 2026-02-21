# RSSdeck-MCP

An MCP (Model Context Protocol) server that transforms RSS feeds into token-efficient, AI-ready data for agents like OpenClaw.

[![GitHub Repo](https://img.shields.io/badge/GitHub-mephistophelesbits%2Frssdeck--mcp-blue)](https://github.com/mephistophelesbits/rssdeck-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Overview

RSSdeck-MCP is designed for AI agents that need efficient, structured access to RSS content. Instead of fetching full articles (wasting tokens), it provides:

- **TL;DR Summaries** — Concise 3-bullet summaries, not full text
- **Deduplication** — Removes duplicate stories across feeds
- **Relevance Scoring** — Filters by your interests
- **Sentiment Analysis** — Bullish/bearish/neutral classification

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   RSS Sources   │────▶│   RSSdeck-MCP    │────▶│  AI Agent       │
│   (30+ feeds)   │     │  (This Server)   │     │  (OpenClaw)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Token-Efficient │
                        │  Summaries        │
                        └──────────────────┘
```

## Relationship to RSSdeck

**RSSdeck** (the main project) is a human-facing RSS reader:
- Web UI with multi-column TweetDeck-style layout
- Local AI integration (Ollama) for summaries
- Full article scraping
- For humans who want to read RSS manually

**RSSdeck-MCP** is an agent-facing data service:
- MCP server for AI agents
- Token-efficient API responses
- No UI — purely programmatic
- For AI agents that need RSS data

**They work together:**
1. Add feeds in RSSdeck (web UI)
2. Export to OPML
3. RSSdeck-MCP reads the OPML and serves agents

## Installation

```bash
# Clone the repository
git clone https://github.com/mephistophelesbits/rssdeck-mcp.git
cd rssdeck-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```bash
# RSSdeck instance URL (optional, for future API integration)
RSSDECK_URL=http://localhost:3001

# Your interests - comma separated (used for relevance scoring)
INTERESTS=AI,operations,Malaysia,APAC,business,technology,management

# Path to OPML file (exports from RSSdeck)
RSSDECK_OPML=./feeds/opml/your-feeds.opml
```

## Usage

### Running the MCP Server

```bash
python server.py
```

The server runs on stdio, ready to receive MCP calls from agents.

### Using with OpenClaw

Configure OpenClaw to use RSSdeck-MCP as an RSS data source. The MCP server provides these tools:

| Tool | Description |
|------|-------------|
| `get_feeds` | List all configured RSS feeds |
| `get_updates` | Get latest articles with TL;DR summaries |
| `search` | Search across cached articles |
| `get_summary` | Get detailed summary of a specific article |

### Example Output

```json
{
  "count": 5,
  "articles": [
    {
      "id": "abc123",
      "title": "Karpathy's Claws: The New Layer on AI Agents",
      "source": "Hacker News",
      "published": "2026-02-21T10:30:00Z",
      "tldr": "Andrej Karpathy discusses 'Claws' - AI agents on personal hardware...",
      "sentiment": "bullish",
      "relevance": 0.8,
      "url": "https://news.ycombinator.com/item?id=..."
    }
  ],
  "token_tip": "These are TL;DR summaries, not full articles."
}
```

## Setting Up Feeds

### Method 1: RSSdeck Export (Recommended)

1. Open RSSdeck at http://localhost:3001
2. Add your feeds in the UI
3. Click the **Export OPML** button in the sidebar
4. Save the OPML file to `feeds/opml/`
5. Update `RSSDECK_OPML` in `.env` to point to it

### Method 2: Manual OPML

Create your own OPML file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>My Feeds</title>
  </head>
  <body>
    <outline text="Tech" xmlUrl="https://hnrss.org/frontpage"/>
    <outline text="AI" xmlUrl="https://simonwillison.net/atom/everything/"/>
  </body>
</opml>
```

## Features

### Token Efficiency

- Summaries are capped at ~150 characters
- Full articles are never sent to the agent
- Deduplication reduces redundant content by ~40%

### Relevance Scoring

Articles are scored based on your configured interests:
- 0.0 = irrelevant
- 1.0 = highly relevant

### Sentiment Analysis

Simple keyword-based classification:
- **bullish** — positive tech/business news
- **bearish** — negative news (failures, vulnerabilities)
- **neutral** — factual news

## Use Cases

### Second Brain

Power your personal AI assistant with curated RSS intelligence:
- Daily AI/Tech news summaries
- Industry-specific updates
- Competitor monitoring

### Automation

Feed AI agents structured data for:
- Content generation
- Trend analysis
- Research pipelines

### Monitoring

Track specific topics across many sources:
- Job market intelligence
- Tech industry news
- Competitor updates

## Integration with RSSdeck

```
┌─────────────────────────────────────────────────────────────┐
│                        RSSdeck                                │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │  Add Feeds │───▶│  Export OPML  │───▶│  MCP Server │   │
│  │  (Web UI)  │    │  (Sidebar)    │    │  (This)     │   │
│  └─────────────┘    └──────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Python 3.10+** — Server runtime
- **MCP** — Model Context Protocol
- **httpx** — Async HTTP client
- **feedparser** — RSS/Atom parsing
- **BeautifulSoup** — HTML parsing

## Contributing

Contributions welcome! Please read the [contributing guidelines](CONTRIBUTING.md) first.

## License

MIT License — see [LICENSE](LICENSE) file.

## Related Projects

- **[RSSdeck](https://github.com/mephistophelesbits/rssdeck)** — Human-facing RSS reader with AI integration
- **[OpenClaw](https://github.com/openclaw/openclaw)** — AI agent platform that uses RSSdeck-MCP

## Acknowledgments

- Inspired by [Karpathy's "Claws" concept](https://twitter.com/karpathy/status/2024987174077432126)
- Built to power my second brain with OpenClaw
