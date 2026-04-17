import re
from typing import Optional


class ArticleExtractor:
    """Extracts full article text. Primary: trafilatura. Fallback: requests + BS4."""

    REQUEST_TIMEOUT = 25
    MIN_TEXT_LENGTH = 150

    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,zh;q=0.8,ja;q=0.7',
    }

    def extract(self, url: str) -> Optional[str]:
        """Returns plain text or None if extraction fails."""
        text = self._trafilatura_extract(url)
        if text and len(text) >= self.MIN_TEXT_LENGTH:
            return text
        text = self._bs4_fallback(url)
        if text and len(text) >= self.MIN_TEXT_LENGTH:
            return text
        return None

    def _trafilatura_extract(self, url: str) -> Optional[str]:
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                favor_recall=True,
                no_fallback=False,
            )
            return text
        except Exception:
            return None

    def _bs4_fallback(self, url: str) -> Optional[str]:
        try:
            import requests
            from bs4 import BeautifulSoup
            resp = requests.get(
                url, headers=self.HEADERS,
                timeout=self.REQUEST_TIMEOUT, allow_redirects=True
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'lxml')

            # Remove boilerplate elements
            for tag in soup.select('nav, header, footer, aside, script, style, '
                                   '.advertisement, #comments, .related'):
                tag.decompose()

            # Try known content containers first
            content = None
            for sel in ('article', '[role="main"]', '.article-body',
                        '.story-body', '.entry-content', '#content', 'main'):
                content = soup.select_one(sel)
                if content:
                    break
            if content is None:
                content = soup.body or soup

            paragraphs = [p.get_text(separator=' ', strip=True)
                          for p in content.find_all('p') if p.get_text(strip=True)]
            return '\n\n'.join(paragraphs)
        except Exception:
            return None
