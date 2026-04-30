import json
import math
import re
from datetime import datetime

import customtkinter as ctk

from app.config import APP_DATA_DIR
from app.database.repository import Repository
from app.feed.pipeline import FetchPipeline
from app.feed.scheduler import RefreshScheduler
from app.gui.article_detail import ArticleDetail
from app.gui.article_list import ArticleList
from app.gui.insight_panel import InsightPanel
from app.gui.report_panel import ReportPanel
from app.gui.settings_dialog import SettingsDialog
from app.gui.sidebar import Sidebar
from app.gui.source_health_panel import SourceHealthPanel
from app.gui.toolbar import Toolbar
from app.utils.threading_utils import BackgroundTaskManager


class AppWindow(ctk.CTk):
    TITLE = 'Global News Reader'
    GEOMETRY = '1400x860'

    def __init__(self, repository: Repository, pipeline: FetchPipeline):
        super().__init__()
        self.title(self.TITLE)
        self.geometry(self.GEOMETRY)
        self.minsize(1080, 680)

        self._repo = repository
        self._pipeline = pipeline
        self._task_mgr = BackgroundTaskManager(self)
        self._current_page = 1
        self._search_query = ''
        self._status_filter = 'all'
        self._enabled_source_ids: list[int] | None = None
        self._current_article: dict | None = None
        self._last_stats: dict = {}

        interval = int(self._repo.get_setting('auto_refresh_interval', '0'))
        self._scheduler = RefreshScheduler(
            callback=lambda: self._task_mgr.post_status(
                '__AUTO_REFRESH__', self._on_auto_refresh
            ),
            interval_minutes=interval,
        )

        self._build_layout()
        self._load_sources()
        self._load_articles()

        if interval > 0:
            self._scheduler.start()

        self.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build_layout(self) -> None:
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=0)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=3)
        self.columnconfigure(2, weight=4)

        self._toolbar = Toolbar(
            self,
            on_refresh=self._on_refresh_clicked,
            on_search=self._on_search,
            on_status_filter=self._on_status_filter_change,
            on_ai_analyze=self._on_ai_analyze,
            on_settings=self._open_settings,
        )
        self._toolbar.grid(row=0, column=0, columnspan=3, sticky='ew')

        self._insight = InsightPanel(
            self,
            on_status_filter=self._on_status_filter_change,
            on_analyze_queue=self._on_analyze_queue,
            on_extract_missing=self._on_extract_missing,
            on_generate_report=self._on_generate_topic_report,
        )
        self._insight.grid(row=1, column=0, columnspan=3, sticky='ew')

        self._sidebar = Sidebar(self, on_filter_change=self._on_filter_change)
        self._sidebar.grid(row=2, column=0, sticky='nsew', padx=(6, 3), pady=6)

        self._article_list = ArticleList(self, on_select=self._on_article_selected)
        self._article_list.grid(row=2, column=1, sticky='nsew', padx=3, pady=6)

        self._right_tabs = ctk.CTkTabview(self)
        self._right_tabs.grid(row=2, column=2, sticky='nsew', padx=(3, 6), pady=6)
        self._right_tabs.add('Article')
        self._right_tabs.add('Reports')
        self._right_tabs.add('Source Health')
        article_tab = self._right_tabs.tab('Article')
        article_tab.rowconfigure(0, weight=1)
        article_tab.columnconfigure(0, weight=1)
        reports_tab = self._right_tabs.tab('Reports')
        reports_tab.rowconfigure(0, weight=1)
        reports_tab.columnconfigure(0, weight=1)
        health_tab = self._right_tabs.tab('Source Health')
        health_tab.rowconfigure(0, weight=1)
        health_tab.columnconfigure(0, weight=1)

        self._article_detail = ArticleDetail(
            article_tab,
            on_extract_text=self._on_extract_text,
            on_analyze=self._on_ai_analyze_article,
            on_toggle_favorite=self._on_toggle_favorite,
            on_mark_unread=self._on_mark_unread,
            on_export_markdown=self._on_export_markdown,
        )
        self._article_detail.grid(row=0, column=0, sticky='nsew')

        self._report_panel = ReportPanel(
            reports_tab,
            on_generate=self._on_generate_topic_report,
            on_export=self._on_export_report_markdown,
        )
        self._report_panel.grid(row=0, column=0, sticky='nsew')

        self._source_health_panel = SourceHealthPanel(
            health_tab,
            on_cleanup=self._on_cleanup_now,
        )
        self._source_health_panel.grid(row=0, column=0, sticky='nsew')

        self._status_bar = ctk.CTkFrame(self, height=32, corner_radius=0,
                                         fg_color=('gray85', 'gray20'))
        self._status_bar.grid(row=3, column=0, columnspan=3, sticky='ew')
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
            status_filter=self._status_filter,
        )

        total_pages = max(1, math.ceil(total / per_page))
        if self._current_page > total_pages:
            self._current_page = total_pages
            articles, total = self._repo.get_articles(
                source_ids=self._enabled_source_ids,
                search_query=self._search_query or None,
                page=self._current_page,
                per_page=per_page,
                status_filter=self._status_filter,
            )

        selected_id = self._current_article.get('id') if self._current_article else None
        self._article_list.display(
            articles, total, self._current_page, per_page,
            on_page_change=self._on_page_change,
            selected_id=selected_id,
            status_filter=self._status_filter,
        )
        self._refresh_insights()
        self._load_reports()
        self._load_source_health()

    def _load_reports(self) -> None:
        self._report_panel.display_reports(self._repo.get_topic_reports(limit=30))

    def _load_source_health(self) -> None:
        self._source_health_panel.display(
            self._repo.get_source_health(),
            self._repo.get_all_settings(),
        )

    def _refresh_insights(self) -> None:
        self._last_stats = self._repo.get_article_stats(
            source_ids=self._enabled_source_ids,
            search_query=self._search_query or None,
        )
        self._insight.update_stats(self._last_stats, self._status_filter)
        total = int(self._last_stats.get('total') or 0)
        unread = int(self._last_stats.get('unread') or 0)
        saved = int(self._last_stats.get('favorites') or 0)
        self._count_lbl.configure(text=f'{total} articles | {unread} unread | {saved} saved')

    def _on_refresh_clicked(self) -> None:
        self._start_fetch('Fetching news...')

    def _on_auto_refresh(self, _msg: str) -> None:
        self._start_fetch('Auto-refreshing news...')

    def _start_fetch(self, status: str) -> None:
        sources = self._repo.get_sources(enabled_only=True)
        if not sources:
            self._set_status('No enabled sources. Enable at least one source in Settings.')
            return
        self._toolbar.set_busy(True)
        self._set_status(status, busy=True)
        extract = self._repo.get_setting('extract_full_text', '1') == '1'
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
            msg += f' | {len(errors)} error{"s" if len(errors) != 1 else ""}'
        cleanup = result.get('cleanup') or {}
        if cleanup.get('deleted_total'):
            msg += f" | cleaned {cleanup['deleted_total']}"
        self._set_status(msg)
        self._load_articles()
        self._load_source_health()

        if new and self._repo.get_setting('auto_analyze', '0') == '1':
            self._on_analyze_queue()
        if new and self._repo.get_setting('auto_topic_reports', '0') == '1':
            self._on_generate_topic_report(silent=True)

    def _on_rss_stage_done(self, _msg: str) -> None:
        self._load_articles()

    def _on_fetch_error(self, error: Exception) -> None:
        self._toolbar.set_busy(False)
        self._set_status(f'Fetch error: {error}')

    def _on_filter_change(self, enabled_ids: list[int]) -> None:
        self._enabled_source_ids = enabled_ids
        self._current_page = 1
        self._load_articles()

    def _on_status_filter_change(self, status_filter: str) -> None:
        self._status_filter = status_filter
        self._toolbar.set_status_filter(status_filter)
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
        if not article.get('is_read'):
            self._repo.set_article_read(article['id'], True)
            article['is_read'] = 1
            self._article_list.mark_article_read(article['id'], True)

        self._current_article = article
        self._article_detail.display_article(article)
        self._toolbar.enable_ai_button(True)
        self._refresh_insights()

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
                self._current_article = updated
                self._article_detail.update_full_text(updated.get('full_text', ''))
            self._refresh_insights()

    def _on_extract_text(self, article: dict) -> None:
        self._set_status('Extracting article text...')
        self._task_mgr.submit(
            self._pipeline.extract_article_text,
            article['id'], article['url'],
            on_done=lambda ok: self._on_text_extracted(article, ok),
            on_error=lambda e: self._set_status(f'Extract error: {e}'),
        )

    def _on_extract_missing(self) -> None:
        self._set_status('Extracting missing full text...', busy=True)
        self._task_mgr.submit(
            self._do_extract_missing,
            on_done=self._on_extract_missing_done,
            on_error=lambda e: self._set_status(f'Extract queue error: {e}'),
        )

    def _do_extract_missing(self) -> dict:
        def progress(msg, done, total):
            self._task_mgr.post_status(
                f'[{done}/{total}] {msg}',
                self._set_status,
            )
        return self._pipeline.extract_missing_texts(progress_callback=progress)

    def _on_extract_missing_done(self, result: dict) -> None:
        errors = result.get('errors', [])
        msg = f"Text extraction queue finished ({result.get('extracted', 0)} checked)"
        if errors:
            msg += f" | {len(errors)} errors"
        self._set_status(msg)
        self._load_articles()
        self._load_source_health()
        self._reload_current_article()

    def _on_cleanup_now(self) -> None:
        if self._repo.get_setting('cleanup_enabled', '1') != '1':
            self._set_status('Cleanup is disabled in Settings.')
            return
        self._set_status('Running article cleanup...', busy=True)
        self._task_mgr.submit(
            self._pipeline.run_cleanup,
            on_done=self._on_cleanup_done,
            on_error=lambda e: self._set_status(f'Cleanup error: {e}'),
        )

    def _on_cleanup_done(self, result: dict) -> None:
        self._set_status(
            f"Cleanup complete: {result.get('deleted_total', 0)} articles removed"
        )
        self._load_articles()
        self._load_source_health()

    def _on_ai_analyze(self) -> None:
        if self._current_article:
            self._on_ai_analyze_article(self._current_article)

    def _on_ai_analyze_article(self, article: dict) -> None:
        self._set_status('Analyzing selected article with AI...', busy=True)
        self._task_mgr.submit(
            self._do_ai_analysis, article,
            on_done=lambda result: self._on_analysis_done(article, result),
            on_error=lambda e: self._set_status(f'AI error: {e}'),
        )

    def _do_ai_analysis(self, article: dict) -> str:
        from app.ai.base import get_provider

        provider = get_provider(self._repo.get_all_settings())
        analysis_json = self._analyze_with_provider(provider, article)
        self._repo.update_article_ai_analysis(article['id'], analysis_json)
        return analysis_json

    def _on_analyze_queue(self) -> None:
        articles = self._repo.get_articles_for_ai(
            source_ids=self._enabled_source_ids,
            search_query=self._search_query or None,
            limit=5,
        )
        if not articles:
            self._set_status('No articles need AI analysis in the current view.')
            return
        self._set_status(f'Analyzing briefing queue ({len(articles)} articles)...', busy=True)
        self._task_mgr.submit(
            self._do_ai_analysis_queue,
            articles,
            on_done=self._on_analysis_queue_done,
            on_error=lambda e: self._set_status(f'AI queue error: {e}'),
        )

    def _do_ai_analysis_queue(self, articles: list[dict]) -> dict:
        from app.ai.base import get_provider

        provider = get_provider(self._repo.get_all_settings())
        errors: list[str] = []
        analyzed = 0
        total = len(articles)

        for idx, article in enumerate(articles, start=1):
            self._task_mgr.post_status(
                f'[{idx}/{total}] AI briefing: {article.get("title", "")[:60]}',
                self._set_status,
            )
            try:
                analysis_json = self._analyze_with_provider(provider, article)
                self._repo.update_article_ai_analysis(article['id'], analysis_json)
                analyzed += 1
            except Exception as e:
                errors.append(f"{article.get('title', 'Untitled')}: {e}")

        return {'analyzed': analyzed, 'errors': errors}

    def _analyze_with_provider(self, provider, article: dict) -> str:
        text = article.get('full_text') or article.get('summary') or article.get('title', '')
        result = provider.analyze_article(
            title=article.get('title', ''),
            text=text,
            language=article.get('language', 'en'),
            output_language=self._repo.get_setting('ai_report_language', 'English'),
        )
        return json.dumps({
            'summary': result.summary,
            'keywords': result.keywords,
            'sentiment': result.sentiment,
            'confidence': result.confidence,
            'provider': result.provider,
            'model': result.model,
            'analyzed_at': result.analyzed_at,
            'language': self._repo.get_setting('ai_report_language', 'English'),
        }, ensure_ascii=False)

    def _on_generate_topic_report(self, silent: bool = False) -> None:
        keywords = self._topic_keywords()
        if not keywords:
            if self._search_query.strip():
                keywords = [self._search_query.strip()]
            else:
                if not silent:
                    self._set_status('Configure Topic Keywords in Settings, or search for a topic first.')
                return

        limit = self._int_setting('topic_report_max_articles', 10)
        articles = self._repo.get_articles_matching_keywords(
            keywords,
            source_ids=self._enabled_source_ids,
            limit=limit,
        )
        if not articles:
            if not silent:
                self._set_status('No articles match the configured topic keywords.')
            return

        title = self._topic_title(keywords)
        language = self._repo.get_setting('ai_report_language', 'English')
        self._set_status(f'Generating topic report: {title}', busy=True)
        self._task_mgr.submit(
            self._do_generate_topic_report,
            title,
            keywords,
            articles,
            language,
            on_done=self._on_topic_report_done,
            on_error=lambda e: self._set_status(f'Topic report error: {e}'),
        )

    def _do_generate_topic_report(
        self,
        title: str,
        keywords: list[str],
        articles: list[dict],
        language: str,
    ) -> int:
        from app.ai.base import get_provider

        provider = get_provider(self._repo.get_all_settings())
        result = provider.generate_topic_report(
            title=title,
            keywords=keywords,
            articles=articles,
            output_language=language,
        )
        return self._repo.create_topic_report(
            title=title,
            keywords=keywords,
            language=language,
            article_ids=[a['id'] for a in articles],
            report=result.report,
            provider=result.provider,
            model=result.model,
        )

    def _on_topic_report_done(self, report_id: int) -> None:
        report = self._repo.get_topic_report_by_id(report_id)
        self._load_reports()
        if report:
            self._report_panel.select_report(report)
        self._right_tabs.set('Reports')
        self._set_status('Topic report generated')

    def _on_analysis_done(self, article: dict, analysis_json: str) -> None:
        self._set_status('AI analysis complete')
        if self._current_article and self._current_article.get('id') == article['id']:
            self._current_article['ai_analysis'] = analysis_json
            self._article_detail.update_analysis(analysis_json)
        self._load_articles()

    def _on_analysis_queue_done(self, result: dict) -> None:
        errors = result.get('errors', [])
        msg = f"AI queue complete: {result.get('analyzed', 0)} analyzed"
        if errors:
            msg += f" | {len(errors)} errors"
        self._set_status(msg)
        self._load_articles()
        self._reload_current_article()

    def _on_toggle_favorite(self, article: dict, is_favorite: bool) -> None:
        self._repo.set_article_favorite(article['id'], is_favorite)
        if self._current_article and self._current_article.get('id') == article['id']:
            self._current_article['is_favorite'] = int(is_favorite)
            self._article_detail.update_favorite(is_favorite)
        self._set_status('Article saved' if is_favorite else 'Article removed from saved')
        self._load_articles()

    def _on_mark_unread(self, article: dict) -> None:
        self._repo.set_article_read(article['id'], False)
        if self._current_article and self._current_article.get('id') == article['id']:
            self._current_article['is_read'] = 0
            self._article_detail.update_read(False)
        self._article_list.mark_article_read(article['id'], False)
        self._set_status('Marked as unread')
        self._refresh_insights()

    def _on_export_markdown(self, article: dict) -> None:
        export_dir = APP_DATA_DIR / 'exports'
        export_dir.mkdir(parents=True, exist_ok=True)

        title = article.get('title') or 'untitled'
        date_part = (article.get('published_at') or article.get('fetched_at') or '')[:10]
        safe_title = re.sub(r'[\\/:*?"<>|]+', '', title).strip()[:72] or 'article'
        path = export_dir / f'{date_part}_{safe_title}.md'

        ai = self._parse_ai(article.get('ai_analysis'))
        keywords = ', '.join(ai.get('keywords', [])) if ai else ''
        summary = ai.get('summary') if ai else article.get('summary', '')
        body = article.get('full_text') or article.get('summary') or ''
        content = [
            f'# {title}',
            '',
            f"- Source: {article.get('source_name', '')}",
            f"- Published: {article.get('published_at', '')}",
            f"- URL: {article.get('url', '')}",
        ]
        if summary:
            content += ['', '## Brief', '', summary]
        if keywords:
            content += ['', f'Keywords: {keywords}']
        if body:
            content += ['', '## Full Text', '', body]

        path.write_text('\n'.join(content), encoding='utf-8')
        self._set_status(f'Exported Markdown: {path}')

    def _on_export_report_markdown(self, report: dict) -> None:
        export_dir = APP_DATA_DIR / 'reports'
        export_dir.mkdir(parents=True, exist_ok=True)

        title = report.get('title') or 'topic-report'
        safe_title = re.sub(r'[\\/:*?"<>|]+', '', title).strip()[:72] or 'topic-report'
        date_part = (report.get('created_at') or datetime.now().isoformat())[:10]
        path = export_dir / f'{date_part}_{safe_title}.md'
        path.write_text(report.get('report', ''), encoding='utf-8')
        self._set_status(f'Exported report: {path}')

    def _reload_current_article(self) -> None:
        if not self._current_article:
            return
        updated = self._repo.get_article_by_id(self._current_article['id'])
        if updated:
            self._current_article = updated
            self._article_detail.display_article(updated)

    def _open_settings(self) -> None:
        SettingsDialog(self, self._repo, on_save=self._on_settings_saved)

    def _on_settings_saved(self, new_settings: dict) -> None:
        theme = new_settings.get('theme', 'dark')
        ctk.set_appearance_mode(theme)
        interval = int(new_settings.get('auto_refresh_interval', '0'))
        self._scheduler.set_interval(interval)
        self._load_sources()
        self._load_articles()
        self._load_reports()
        self._load_source_health()

    def _set_status(self, msg: str, busy: bool = False) -> None:
        self._status_lbl.configure(text=msg)

    @staticmethod
    def _parse_ai(raw: str | None) -> dict:
        if not raw:
            return {}

    def _topic_keywords(self) -> list[str]:
        raw = self._repo.get_setting('topic_report_keywords', '')
        return [item.strip() for item in re.split(r'[,\n;；，]+', raw) if item.strip()]

    @staticmethod
    def _topic_title(keywords: list[str]) -> str:
        visible = ', '.join(keywords[:3])
        if len(keywords) > 3:
            visible += f' +{len(keywords) - 3}'
        return f'Topic Report: {visible}'

    def _int_setting(self, key: str, default: int) -> int:
        try:
            return int(self._repo.get_setting(key, str(default)))
        except ValueError:
            return default
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _on_close(self) -> None:
        self._scheduler.stop()
        self._task_mgr.shutdown()
        self._repo.close()
        self.destroy()
