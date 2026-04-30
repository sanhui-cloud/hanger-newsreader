from dataclasses import dataclass
from typing import Optional
import feedparser
from app.utils.date_utils import parse_feed_date


@dataclass
class RawEntry:
    title: str
    url: str
    summary: str
    published_at: Optional[str]
    source_id: int


class FeedFetcher:
    REQUEST_TIMEOUT = 20

    def fetch_source(self, source: dict, timeout: int = REQUEST_TIMEOUT) -> list[RawEntry]:
        """Parse one RSS source. Returns list of RawEntry."""
        try:
            feed = feedparser.parse(source['url'], request_headers={
                'User-Agent': 'Mozilla/5.0 (compatible; GlobalNewsReader/1.0)',
                'Accept': 'application/rss+xml, application/atom+xml, text/xml',
            })
        except Exception as e:
            raise RuntimeError(f"Feed parse failed: {e}") from e

        entries = []
        for entry in feed.entries:
            title = getattr(entry, 'title', '').strip()
            url = (getattr(entry, 'link', None)
                   or getattr(entry, 'id', None) or '').strip()
            if not title or not url or not url.startswith('http'):
                continue

            summary = ''
            for attr in ('summary', 'description', 'content'):
                val = getattr(entry, attr, None)
                if val:
                    if isinstance(val, list):
                        val = val[0].get('value', '') if val else ''
                    summary = _strip_html(str(val))[:500]
                    break

            entries.append(RawEntry(
                title=title,
                url=url,
                summary=summary,
                published_at=parse_feed_date(entry),
                source_id=source['id'],
            ))

        if not entries and getattr(feed, 'bozo', False):
            err = getattr(feed, 'bozo_exception', 'unknown feed parse error')
            raise RuntimeError(str(err))

        return entries


def _strip_html(text: str) -> str:
    """Remove HTML tags from RSS summary snippets."""
    import re
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
