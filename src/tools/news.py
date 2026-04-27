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


_SUPPLY_CHAIN_KEYWORDS = {
    "port", "shipping", "cargo", "vessel", "freight", "logistics",
    "hurricane", "storm", "flood", "earthquake", "disruption",
    "strike", "blockade", "closure", "delay", "container", "trade",
    "export", "import", "supply chain", "harbor", "harbour",
}


def get_local_news(city: str, country_code: str, lang: str = "en", max_results: int = 8) -> list[dict]:
    """Fetch country-specific RSS news relevant to a port city.

    Returns articles that mention the city OR supply-chain keywords, sourced
    from country-specific feeds. Returns empty list if no country feeds are
    configured — never falls back to global/BBC feeds so unrelated headlines
    don't appear under a city.
    """
    import json as _json
    from pathlib import Path
    _feeds_path = Path(__file__).parent.parent.parent / "backend" / "data" / "country_feeds.json"
    try:
        country_feeds = _json.loads(_feeds_path.read_text(encoding="utf-8"))
    except Exception:
        country_feeds = {}

    code = (country_code or "").upper()
    feed_list = country_feeds.get(code, [])
    if not feed_list:
        # No country-specific feeds — return nothing rather than unrelated global news
        return []

    sources = [f"{code}" ] * len(feed_list)
    all_entries: list[dict] = []
    with ThreadPoolExecutor(max_workers=min(len(feed_list), 6)) as executor:
        futures = {executor.submit(_fetch_feed, src, url): url for src, url in zip(sources, feed_list)}
        for future in as_completed(futures):
            all_entries.extend(future.result())

    city_lower = city.lower()
    seen_links: set[str] = set()
    city_matches: list[dict] = []
    supply_matches: list[dict] = []

    for entry in all_entries:
        link = entry.get("link", "")
        if link in seen_links:
            continue
        text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
        article = {
            "title": entry.get("title", ""),
            "link": link,
            "summary": entry.get("summary", ""),
            "source": entry.get("source", ""),
        }
        if city_lower in text:
            seen_links.add(link)
            city_matches.append(article)
        elif any(kw in text for kw in _SUPPLY_CHAIN_KEYWORDS):
            seen_links.add(link)
            supply_matches.append(article)
        if len(city_matches) >= max_results:
            break

    # City-specific matches first, then supply-chain relevant from the same country
    combined = city_matches + supply_matches
    return combined[:max_results]


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
