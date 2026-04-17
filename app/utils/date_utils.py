import re
from datetime import datetime, timezone
from typing import Optional
import time


def parse_feed_date(entry) -> Optional[str]:
    """
    Extract and normalize publish date from a feedparser entry to ISO8601 string.
    Tries published_parsed, updated_parsed, in that order.
    """
    for attr in ('published_parsed', 'updated_parsed'):
        val = getattr(entry, attr, None)
        if val and isinstance(val, time.struct_time):
            try:
                dt = datetime(*val[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                continue
    return None


def relative_time(iso_str: Optional[str]) -> str:
    """Convert ISO8601 string to human-readable relative time (e.g. '2h ago')."""
    if not iso_str:
        return ''
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        # Make both tz-aware for subtraction
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 0:
            return 'just now'
        if seconds < 60:
            return f'{seconds}s ago'
        if seconds < 3600:
            return f'{seconds // 60}m ago'
        if seconds < 86400:
            return f'{seconds // 3600}h ago'
        if seconds < 86400 * 7:
            return f'{seconds // 86400}d ago'
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return iso_str[:10] if iso_str else ''


def format_date(iso_str: Optional[str], fmt: str = '%Y-%m-%d %H:%M') -> str:
    """Format ISO8601 string for display."""
    if not iso_str:
        return ''
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime(fmt)
    except Exception:
        return iso_str[:16] if iso_str else ''
