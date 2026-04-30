import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from app.feed.fetcher import FeedFetcher
from app.feed.extractor import ArticleExtractor
from app.database.repository import Repository


class FetchPipeline:
    """Orchestrates RSS fetch → dedup → store → (optional) full text extract."""

    def __init__(
        self,
        repository: Repository,
        fetcher: Optional[FeedFetcher] = None,
        extractor: Optional[ArticleExtractor] = None,
        max_fetch_workers: int = 5,
        max_extract_workers: int = 3,
    ):
        self._repo = repository
        self._fetcher = fetcher or FeedFetcher()
        self._extractor = extractor or ArticleExtractor()
        self._max_fetch = max_fetch_workers
        self._max_extract = max_extract_workers
        self._extract_semaphore = threading.Semaphore(max_extract_workers)

    def run_full_fetch(
        self,
        sources: list[dict],
        extract_full_text: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        on_rss_done: Optional[Callable] = None,
    ) -> dict:
        """
        Stage 1: Fetch RSS for all enabled sources in parallel.
        Stage 2: Insert new articles to DB.
        Stage 3: Optionally extract full text for new articles.
        Returns {'new_articles': int, 'errors': list[str]}.
        """
        errors: list[str] = []
        new_article_ids: list[tuple[int, str]] = []  # (id, url)
        total_sources = len(sources)

        def _report(msg: str, done: int) -> None:
            if progress_callback:
                progress_callback(msg, done, total_sources)

        # Stage 1+2: Fetch RSS and store
        with ThreadPoolExecutor(max_workers=self._max_fetch) as pool:
            futures = {
                pool.submit(self._fetcher.fetch_source, src): src
                for src in sources
            }
            done = 0
            for future in as_completed(futures):
                src = futures[future]
                done += 1
                _report(f"Fetching {src['name']}...", done)
                try:
                    entries = future.result()
                except Exception as e:
                    errors.append(f"{src['name']}: {e}")
                    self._repo.update_source_fetch_result(
                        src['id'], success=False, error=str(e)
                    )
                    continue

                new_for_source = 0
                for entry in entries:
                    article_id = self._repo.insert_article(
                        source_id=entry.source_id,
                        title=entry.title,
                        url=entry.url,
                        summary=entry.summary,
                        published_at=entry.published_at,
                    )
                    if article_id is not None:
                        new_article_ids.append((article_id, entry.url))
                        new_for_source += 1

                last_entry_at = self._newest_entry_date(entries)
                self._repo.update_source_fetch_result(
                    src['id'],
                    success=True,
                    new_count=new_for_source,
                    entry_count=len(entries),
                    last_entry_at=last_entry_at,
                )

                # Trim old articles for this source
                max_keep = int(self._repo.get_setting('max_articles_per_source', '100'))
                self._repo.delete_old_articles(src['id'], max_keep)

        # Notify GUI that RSS stage is done — articles can be displayed now
        if on_rss_done:
            on_rss_done()

        # Stage 3: Extract full text
        if extract_full_text and new_article_ids:
            total_extract = len(new_article_ids)
            _report(f"Extracting full text for {total_extract} articles...", total_sources)

            with ThreadPoolExecutor(max_workers=self._max_extract) as pool:
                futures = {
                    pool.submit(self.extract_article_text, aid, url): (aid, url)
                    for aid, url in new_article_ids
                }
                done = 0
                for future in as_completed(futures):
                    done += 1
                    aid, url = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        errors.append(f"Extract {url[:60]}: {e}")
                    if done % 5 == 0:
                        _report(f"Extracting full text ({done}/{total_extract})...",
                                total_sources)

        cleanup_result = {}
        if self._repo.get_setting('cleanup_enabled', '1') == '1' and \
           self._repo.get_setting('cleanup_on_refresh', '1') == '1':
            cleanup_result = self.run_cleanup()

        _report("Done", total_sources)
        return {
            'new_articles': len(new_article_ids),
            'errors': errors,
            'cleanup': cleanup_result,
        }

    def run_cleanup(self) -> dict:
        return self._repo.cleanup_articles(
            max_age_days=self._int_setting('max_article_age_days', 90),
            max_total_articles=self._int_setting('max_total_articles', 2000),
            max_articles_per_source=self._int_setting('max_articles_per_source', 100),
        )

    def extract_article_text(self, article_id: int, url: str) -> bool:
        """Extract and store full text for one article. Returns True if successful."""
        with self._extract_semaphore:
            text = self._extractor.extract(url)
            if text:
                self._repo.update_article_full_text(article_id, text)
                return True
            return False

    def extract_missing_texts(
        self,
        source_id: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> dict:
        """Re-extract full text for articles that don't have it yet."""
        articles = self._repo.get_articles_needing_extraction(source_id, limit=50)
        total = len(articles)
        errors: list[str] = []

        with ThreadPoolExecutor(max_workers=self._max_extract) as pool:
            futures = {
                pool.submit(self.extract_article_text, a['id'], a['url']): a
                for a in articles
            }
            done = 0
            for future in as_completed(futures):
                done += 1
                a = futures[future]
                if progress_callback:
                    progress_callback(f"Extracting ({done}/{total})...", done, total)
                try:
                    future.result()
                except Exception as e:
                    errors.append(f"{a['url'][:60]}: {e}")

        return {'extracted': total, 'errors': errors}

    @staticmethod
    def _newest_entry_date(entries) -> Optional[str]:
        dates = [entry.published_at for entry in entries if entry.published_at]
        return max(dates) if dates else None

    def _int_setting(self, key: str, default: int) -> int:
        try:
            return int(self._repo.get_setting(key, str(default)))
        except ValueError:
            return default
