# RSSdeck-MCP

MCP (Model Context Protocol) server for AI agents - token-efficient RSS data for OpenClaw and other agents.

## Features

- **TL;DR Summaries** - Don't get full articles, get 3-bullet summaries
- **Deduplication** - Remove duplicate stories across feeds
- **Interest Matching** - Filter by relevance to user interests
- **Delta Updates** - Only get new content since last check
- **Structured Output** - JSON, ready for AI consumption

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_feeds` | List all configured feeds |
| `get_updates` | Get latest articles with summaries |
| `search` | Search across all cached articles |
| `get_summary` | Get a specific article's summary |

## Environment

```
RSSDECK_URL=http://localhost:3001  # Your RSSdeck instance
INTERESTS=AI,operations,Malaysia    # Comma-separated interests
```

## Architecture

```
AI Agent (OpenClaw)
      ↓
   MCP Server (this)
      ↓
   RSSdeck API (fetch/parse)
      ↓
   Smart Layer (dedupe, summarize, filter)
      ↓
   Token-efficient response
```

## Why V2?

V1 is human-focused (UI, dashboards). V2 is agent-focused (APIs, MCP, token efficiency).

Built by Fong to solve: "How do I give my AI agent the right information without blowing through tokens?"
