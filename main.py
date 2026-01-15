# src/rss.py
import asyncio, aiohttp, feedparser, logging, warnings
from typing import List
from datetime import datetime
from charset_normalizer import from_bytes
from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

RSS_FALLBACK = [
    "http://www.boannews.com/media/news_rss.xml?mkind=1",
    "http://www.boannews.com/media/news_rss.xml?mkind=2",
    "http://www.boannews.com/media/news_rss.xml?mkind=3",
    "http://www.boannews.com/media/news_rss.xml?mkind=4",
    "http://www.boannews.com/media/news_rss.xml?mkind=5",
    "http://www.boannews.com/media/news_rss.xml?kind=1",
    "http://www.boannews.com/media/news_rss.xml?kind=2",
    "http://www.boannews.com/media/news_rss.xml?kind=3",
    "http://www.boannews.com/media/news_rss.xml?kind=4",
    "http://www.boannews.com/media/news_rss.xml?kind=5",
    "http://www.boannews.com/media/news_rss.xml?kind=6",
    "http://www.boannews.com/media/news_rss.xml?skind=2",
    "http://www.boannews.com/media/news_rss.xml?skind=3",
    "http://www.boannews.com/media/news_rss.xml?skind=5",
    "http://www.boannews.com/media/news_rss.xml?skind=6",
    "http://www.boannews.com/media/news_rss.xml?skind=7",
]

def parse_published(entry) -> datetime:
    try:
        if getattr(entry, "published_parsed", None):
            return datetime(*entry.published_parsed[:6])
        if getattr(entry, "updated_parsed", None):
            return datetime(*entry.updated_parsed[:6])
    except Exception:
        pass
    return datetime.now()

async def parse_rss(session, url):
    async with session.get(url, timeout=10) as r:
        content = await r.read()
        text = str(from_bytes(content).best() or content.decode("utf-8", "ignore"))
        feed = feedparser.parse(text)
        return feed.entries or []

async def fetch_single(session, url):
    entries = await parse_rss(session, url)
    result = []
    for e in entries:
        link = getattr(e, "link", None)
        if not link:
            continue
        result.append({
            "title": getattr(e, "title", None),
            "link": link,
            "published": parse_published(e),
            "summary": getattr(e, "summary", None),
            "source": "boannews",
            "category": url,
            "author": getattr(e, "author", None),
        })
    return result

async def fetch_all_entries() -> List[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_single(session, u) for u in RSS_FALLBACK]
        results = await asyncio.gather(*tasks)

    seen, merged = set(), []
    for lst in results:
        for a in lst:
            if a["link"] in seen:
                continue
            seen.add(a["link"])
            merged.append(a)

    return merged

