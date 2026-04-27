import json
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.tool import Tool

FEEDS = [
    ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("GDACS", "https://www.gdacs.org/xml/rss.xml"),
    ("NHC", "https://www.nhc.noaa.gov/index-at.xml"),
    ("Reuters", "https://feeds.reuters.com/reuters/worldNews"),
]


def _fetch_feed(source: str, url: str) -> list[dict]:
    """Fetch and parse a single RSS feed. Returns a list of entry dicts with source tag."""
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries:
            entries.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "published": entry.get("published", ""),
                "link": entry.get("link", ""),
                "source": source,
            })
        return entries
    except Exception:
        return []


def get_news(query: str) -> str:
    # Fan-out: fetch all feeds in parallel
    all_entries: list[dict] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_fetch_feed, source, url): source for source, url in FEEDS}
        for future in as_completed(futures):
            all_entries.extend(future.result())

    terms = query.lower().split()

    # Filter by query terms and dedupe by link
    seen_links: set[str] = set()
    matches: list[dict] = []
    for entry in all_entries:
        link = entry.get("link", "")
        if link in seen_links:
            continue
        text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
        if any(term in text for term in terms):
            seen_links.add(link)
            matches.append(entry)
        if len(matches) >= 5:
            break

    if not matches:
        # Fallback: top 2 from each feed, deduped by link
        feed_top: dict[str, list[dict]] = {source: [] for source, _ in FEEDS}
        for entry in all_entries:
            src = entry.get("source", "")
            if src in feed_top and len(feed_top[src]) < 2:
                feed_top[src].append(entry)

        fallback_seen: set[str] = set()
        fallback: list[dict] = []
        for src_entries in feed_top.values():
            for entry in src_entries:
                link = entry.get("link", "")
                if link not in fallback_seen:
                    fallback_seen.add(link)
                    fallback.append(entry)

        return json.dumps(
            {"note": f"No matches for '{query}', showing top headlines", "articles": fallback},
            ensure_ascii=False,
        )

    return json.dumps(matches, ensure_ascii=False)


def get_local_news(city: str, country_code: str, lang: str = "en", max_results: int = 8) -> list[dict]:
    """Fetch local RSS news for a city, filtered by country code. Falls back to global feeds."""
    import json as _json
    from pathlib import Path
    _feeds_path = Path(__file__).parent.parent.parent / "backend" / "data" / "country_feeds.json"
    try:
        country_feeds = _json.loads(_feeds_path.read_text(encoding="utf-8"))
    except Exception:
        country_feeds = {}

    feed_list = country_feeds.get(country_code.upper() if country_code else "", [])
    if not feed_list:
        feed_list = [url for _, url in FEEDS]
        sources = [src for src, _ in FEEDS]
    else:
        sources = [f"Local-{country_code.upper()}"] * len(feed_list)

    all_entries: list[dict] = []
    with ThreadPoolExecutor(max_workers=min(len(feed_list), 6)) as executor:
        futures = {executor.submit(_fetch_feed, src, url): url for src, url in zip(sources, feed_list)}
        for future in as_completed(futures):
            all_entries.extend(future.result())

    city_lower = city.lower()
    seen_links: set[str] = set()
    matches: list[dict] = []
    for entry in all_entries:
        link = entry.get("link", "")
        if link in seen_links:
            continue
        text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
        if city_lower in text:
            seen_links.add(link)
            matches.append({
                "title": entry.get("title", ""),
                "link": link,
                "summary": entry.get("summary", ""),
                "source": entry.get("source", ""),
            })
        if len(matches) >= max_results:
            break

    if not matches:
        for entry in all_entries[:max_results]:
            link = entry.get("link", "")
            if link not in seen_links:
                seen_links.add(link)
                matches.append({
                    "title": entry.get("title", ""),
                    "link": link,
                    "summary": entry.get("summary", ""),
                    "source": entry.get("source", ""),
                })

    return matches


NEWS_TOOL = Tool(
    name="get_news",
    description="Search recent world news headlines. Returns up to 5 matching articles.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search terms, e.g. 'hurricane gulf mexico'",
            }
        },
        "required": ["query"],
    },
    fn=get_news,
)
