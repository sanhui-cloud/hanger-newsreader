import json
import customtkinter as ctk

from app.database.repository import Repository
from app.feed.pipeline import FetchPipeline
from app.feed.scheduler import RefreshScheduler
from app.utils.threading_utils import BackgroundTaskManager
from app.gui.toolbar import Toolbar
from app.gui.sidebar import Sidebar
from app.gui.article_list import ArticleList
from app.gui.article_detail import ArticleDetail
from app.gui.settings_dialog import SettingsDialog


class AppWindow(ctk.CTk):
    TITLE = 'Global News Reader'
    GEOMETRY = '1400x860'

    def __init__(self, repository: Repository, pipeline: FetchPipeline):
        super().__init__()
        self.title(self.TITLE)
        self.geometry(self.GEOMETRY)
        self.minsize(1000, 600)

        self._repo = repository
        self._pipeline = pipeline
        self._task_mgr = BackgroundTaskManager(self)
        self._current_page = 1
        self._search_query = ''
        self._enabled_source_ids: list[int] | None = None
        self._current_article: dict | None = None

        # Auto-refresh scheduler
        interval = int(self._repo.get_setting('auto_refresh_interval', '0'))
        self._scheduler = RefreshScheduler(
            callback=lambda: self._task_mgr.submit(
                self._do_fetch, on_done=self._on_fetch_done,
                on_error=self._on_fetch_error,
            ),
            interval_minutes=interval,
        )

        self._build_layout()
        self._load_sources()
        self._load_articles()

        if interval > 0:
            self._scheduler.start()

        self.protocol('WM_DELETE_WINDOW', self._on_close)

    # ── Layout ────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=3)
        self.columnconfigure(2, weight=4)

        self._toolbar = Toolbar(
            self,
            on_refresh=self._on_refresh_clicked,
            on_search=self._on_search,
            on_ai_analyze=self._on_ai_analyze,
            on_settings=self._open_settings,
        )
        self._toolbar.grid(row=0, column=0, columnspan=3, sticky='ew')

        self._sidebar = Sidebar(self, on_filter_change=self._on_filter_change)
        self._sidebar.grid(row=1, column=0, sticky='nsew', padx=(6, 3), pady=6)

        self._article_list = ArticleList(self, on_select=self._on_article_selected)
        self._article_list.grid(row=1, column=1, sticky='nsew', padx=3, pady=6)

        self._article_detail = ArticleDetail(
            self,
            on_extract_text=self._on_extract_text,
            on_analyze=self._on_ai_analyze_article,
        )
        self._article_detail.grid(row=1, column=2, sticky='nsew', padx=(3, 6), pady=6)

        # Status bar
        self._status_bar = ctk.CTkFrame(self, height=32, corner_radius=0,
                                         fg_color=('gray85', 'gray20'))
        self._status_bar.grid(row=2, column=0, columnspan=3, sticky='ew')
        self._status_bar.grid_propagate(False)
        self._status_bar.columnconfigure(0, weight=1)

        self._status_lbl = ctk.CTkLabel(
            self._status_bar, text='Ready', anchor='w',
            font=ctk.CTkFont(size=11),
        )
        self._status_lbl.grid(row=0, column=0, padx=10, pady=4, sticky='ew')

        self._count_lbl = ctk.CTkLabel(
            self._status_bar, text='', anchor='e',
            text_color='gray', font=ctk.CTkFont(size=11),
        )
        self._count_lbl.grid(row=0, column=1, padx=10, pady=4)

    # ── Data loading ──────────────────────────────────────────────────────

    def _load_sources(self) -> None:
        sources = self._repo.get_sources()
        self._sidebar.set_sources(sources, on_add_source=self._open_settings)
        self._enabled_source_ids = [s['id'] for s in sources if s['enabled']]

    def _load_articles(self) -> None:
        per_page = int(self._repo.get_setting('articles_per_page', '25'))
        articles, total = self._repo.get_articles(
            source_ids=self._enabled_source_ids,
            search_query=self._search_query or None,
            page=self._current_page,
            per_page=per_page,
        )
        self._article_list.display(
            articles, total, self._current_page, per_page,
            on_page_change=self._on_page_change,
        )
        self._count_lbl.configure(text=f'{total} articles')

    # ── Event handlers ────────────────────────────────────────────────────

    def _on_refresh_clicked(self) -> None:
        self._toolbar.set_busy(True)
        self._set_status('Fetching news...', busy=True)
        extract = self._repo.get_setting('extract_full_text', '1') == '1'
        sources = self._repo.get_sources(enabled_only=True)
        self._task_mgr.submit(
            self._do_fetch,
            sources=sources,
            extract=extract,
            on_done=self._on_fetch_done,
            on_error=self._on_fetch_error,
        )

    def _do_fetch(self, sources: list[dict], extract: bool) -> dict:
        def progress(msg, done, total):
            self._task_mgr.post_status(
                f'[{done}/{total}] {msg}',
                self._set_status,
            )
        return self._pipeline.run_full_fetch(
            sources=sources,
            extract_full_text=extract,
            progress_callback=progress,
            on_rss_done=lambda: self._task_mgr.post_status(
                '__RELOAD__', self._on_rss_stage_done
            ),
        )

    def _on_fetch_done(self, result: dict) -> None:
        self._toolbar.set_busy(False)
        new = result.get('new_articles', 0)
        errors = result.get('errors', [])
        msg = f'Fetched {new} new article{"s" if new != 1 else ""}'
        if errors:
            msg += f'  |  {len(errors)} error{"s" if len(errors) != 1 else ""}'
        self._set_status(msg)
        self._load_articles()

    def _on_rss_stage_done(self, _msg: str) -> None:
        """Called as soon as RSS fetch is complete, before full-text extraction finishes."""
        self._load_articles()

    def _on_fetch_error(self, error: Exception) -> None:
        self._toolbar.set_busy(False)
        self._set_status(f'Fetch error: {error}')

    def _on_filter_change(self, enabled_ids: list[int]) -> None:
        self._enabled_source_ids = enabled_ids
        self._current_page = 1
        self._load_articles()

    def _on_search(self, query: str) -> None:
        self._search_query = query
        self._current_page = 1
        self._load_articles()

    def _on_page_change(self, page: int) -> None:
        self._current_page = page
        self._load_articles()

    def _on_article_selected(self, article: dict) -> None:
        self._current_article = article
        self._article_detail.display_article(article)
        self._toolbar.enable_ai_button(True)

        # Auto-extract full text if missing
        if not article.get('full_text') and article.get('url'):
            self._task_mgr.submit(
                self._pipeline.extract_article_text,
                article['id'], article['url'],
                on_done=lambda ok: self._on_text_extracted(article, ok),
            )

    def _on_text_extracted(self, article: dict, success: bool) -> None:
        if success:
            updated = self._repo.get_article_by_id(article['id'])
            if updated and self._current_article and \
               self._current_article.get('id') == article['id']:
                self._article_detail.update_full_text(updated.get('full_text', ''))

    def _on_extract_text(self, article: dict) -> None:
        self._task_mgr.submit(
            self._pipeline.extract_article_text,
            article['id'], article['url'],
            on_done=lambda ok: self._on_text_extracted(article, ok),
        )

    def _on_ai_analyze(self) -> None:
        if self._current_article:
            self._on_ai_analyze_article(self._current_article)

    def _on_ai_analyze_article(self, article: dict) -> None:
        self._set_status('Analyzing with AI...', busy=True)
        self._task_mgr.submit(
            self._do_ai_analysis, article,
            on_done=lambda result: self._on_analysis_done(article, result),
            on_error=lambda e: self._set_status(f'AI error: {e}'),
        )

    def _do_ai_analysis(self, article: dict) -> str:
        from app.ai.base import get_provider, AIProviderError
        settings = self._repo.get_all_settings()
        provider = get_provider(settings)
        text = article.get('full_text') or article.get('summary') or ''
        result = provider.analyze_article(
            title=article.get('title', ''),
            text=text,
            language=article.get('language', 'en'),
        )
        analysis_json = json.dumps({
            'summary': result.summary,
            'keywords': result.keywords,
            'sentiment': result.sentiment,
            'confidence': result.confidence,
            'provider': result.provider,
            'model': result.model,
            'analyzed_at': result.analyzed_at,
        }, ensure_ascii=False)
        self._repo.update_article_ai_analysis(article['id'], analysis_json)
        return analysis_json

    def _on_analysis_done(self, article: dict, analysis_json: str) -> None:
        self._set_status('AI analysis complete')
        if self._current_article and self._current_article.get('id') == article['id']:
            self._article_detail.update_analysis(analysis_json)
        self._article_list.mark_article_analyzed(article['id'])

    # ── Settings ──────────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        SettingsDialog(self, self._repo, on_save=self._on_settings_saved)

    def _on_settings_saved(self, new_settings: dict) -> None:
        # Apply theme change
        theme = new_settings.get('theme', 'dark')
        ctk.set_appearance_mode(theme)
        # Update auto-refresh
        interval = int(new_settings.get('auto_refresh_interval', '0'))
        self._scheduler.set_interval(interval)
        # Reload sidebar (source changes)
        self._load_sources()
        self._load_articles()

    # ── Status bar helpers ────────────────────────────────────────────────

    def _set_status(self, msg: str, busy: bool = False) -> None:
        self._status_lbl.configure(text=msg)

    def _on_close(self) -> None:
        self._scheduler.stop()
        self._task_mgr.shutdown()
        self._repo.close()
        self.destroy()
