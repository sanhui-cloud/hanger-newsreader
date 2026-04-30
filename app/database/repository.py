import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional


class Repository:
    """All database CRUD. Thread-safe via threading.Lock on writes."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._write_lock = threading.Lock()
        self._settings_cache: dict[str, str] = {}
        self._load_settings_cache()

    def close(self) -> None:
        self._conn.close()

    # ── Settings ──────────────────────────────────────────────────────────

    def _load_settings_cache(self) -> None:
        rows = self._conn.execute("SELECT key, value FROM settings").fetchall()
        self._settings_cache = {r['key']: r['value'] for r in rows}

    def get_setting(self, key: str, default: str = '') -> str:
        return self._settings_cache.get(key, default)

    def set_setting(self, key: str, value: str) -> None:
        with self._write_lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
            )
            self._conn.commit()
        self._settings_cache[key] = value

    def get_all_settings(self) -> dict[str, str]:
        return dict(self._settings_cache)

    def bulk_save_settings(self, settings: dict[str, str]) -> None:
        with self._write_lock:
            self._conn.executemany(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                list(settings.items())
            )
            self._conn.commit()
        self._settings_cache.update(settings)

    # ── Sources ───────────────────────────────────────────────────────────

    def get_sources(self, enabled_only: bool = False) -> list[dict]:
        q = "SELECT * FROM sources"
        if enabled_only:
            q += " WHERE enabled = 1"
        q += " ORDER BY category, name"
        return [dict(r) for r in self._conn.execute(q).fetchall()]

    def add_source(self, name: str, url: str, category: str, language: str,
                   custom: bool = True) -> int:
        with self._write_lock:
            cur = self._conn.execute(
                "INSERT INTO sources (name, url, category, language, custom) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, url, category, language, int(custom))
            )
            self._conn.commit()
            return cur.lastrowid

    def update_source(self, source_id: int, **kwargs) -> None:
        allowed = {'name', 'url', 'category', 'language', 'enabled'}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return
        sets = ', '.join(f"{k} = ?" for k in fields)
        with self._write_lock:
            self._conn.execute(
                f"UPDATE sources SET {sets} WHERE id = ?",
                (*fields.values(), source_id)
            )
            self._conn.commit()

    def delete_source(self, source_id: int) -> None:
        with self._write_lock:
            self._conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            self._conn.commit()

    def toggle_source(self, source_id: int, enabled: bool) -> None:
        self.update_source(source_id, enabled=int(enabled))

    def update_source_fetch_result(
        self,
        source_id: int,
        success: bool,
        new_count: int = 0,
        entry_count: int = 0,
        last_entry_at: Optional[str] = None,
        error: str = '',
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._write_lock:
            if success:
                self._conn.execute("""
                    UPDATE sources
                    SET last_fetched_at = ?,
                        last_success_at = ?,
                        last_error = '',
                        last_new_count = ?,
                        last_entry_at = COALESCE(?, last_entry_at),
                        consecutive_failures = 0,
                        last_fetch_status = ?
                    WHERE id = ?
                """, (
                    now, now, int(new_count), last_entry_at,
                    'empty' if entry_count == 0 else 'ok', source_id,
                ))
            else:
                self._conn.execute("""
                    UPDATE sources
                    SET last_fetched_at = ?,
                        last_error = ?,
                        last_new_count = 0,
                        consecutive_failures = COALESCE(consecutive_failures, 0) + 1,
                        last_fetch_status = 'error'
                    WHERE id = ?
                """, (now, error[:500], source_id))
            self._conn.commit()

    # ── Articles ──────────────────────────────────────────────────────────

    def article_exists_by_url(self, url: str) -> bool:
        r = self._conn.execute(
            "SELECT 1 FROM articles WHERE url = ?", (url,)
        ).fetchone()
        return r is not None

    def insert_article(self, source_id: int, title: str, url: str,
                       summary: Optional[str], published_at: Optional[str]) -> Optional[int]:
        """Returns new article id, or None if URL already exists."""
        with self._write_lock:
            try:
                cur = self._conn.execute(
                    "INSERT INTO articles (source_id, title, url, summary, published_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (source_id, title, url, summary, published_at)
                )
                self._conn.commit()
                return cur.lastrowid
            except sqlite3.IntegrityError:
                return None  # duplicate URL

    def update_article_full_text(self, article_id: int, full_text: str) -> None:
        with self._write_lock:
            self._conn.execute(
                "UPDATE articles SET full_text = ? WHERE id = ?",
                (full_text, article_id)
            )
            self._conn.commit()

    def update_article_ai_analysis(self, article_id: int, analysis_json: str) -> None:
        with self._write_lock:
            self._conn.execute(
                "UPDATE articles SET ai_analysis = ? WHERE id = ?",
                (analysis_json, article_id)
            )
            self._conn.commit()

    def set_article_read(self, article_id: int, is_read: bool) -> None:
        with self._write_lock:
            self._conn.execute(
                "UPDATE articles SET is_read = ?, read_at = CASE WHEN ? THEN datetime('now') ELSE NULL END "
                "WHERE id = ?",
                (int(is_read), int(is_read), article_id),
            )
            self._conn.commit()

    def set_article_favorite(self, article_id: int, is_favorite: bool) -> None:
        with self._write_lock:
            self._conn.execute(
                "UPDATE articles SET is_favorite = ? WHERE id = ?",
                (int(is_favorite), article_id),
            )
            self._conn.commit()

    def _build_article_filters(
        self,
        source_ids: Optional[list[int]] = None,
        search_query: Optional[str] = None,
        status_filter: str = "all",
    ) -> tuple[list[str], list]:
        conditions = []
        params: list = []

        if source_ids is not None:
            if not source_ids:
                conditions.append("0")
            else:
                placeholders = ','.join('?' * len(source_ids))
                conditions.append(f"a.source_id IN ({placeholders})")
                params.extend(source_ids)

        if search_query:
            conditions.append(
                "(a.title LIKE ? OR COALESCE(a.summary, '') LIKE ? "
                "OR COALESCE(a.full_text, '') LIKE ? OR s.name LIKE ?)"
            )
            pattern = f"%{search_query}%"
            params.extend([pattern, pattern, pattern, pattern])

        if status_filter == "unread":
            conditions.append("COALESCE(a.is_read, 0) = 0")
        elif status_filter == "favorites":
            conditions.append("COALESCE(a.is_favorite, 0) = 1")
        elif status_filter == "analyzed":
            conditions.append("COALESCE(a.ai_analysis, '') <> ''")

        return conditions, params

    def get_articles(
        self,
        source_ids: Optional[list[int]] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
        status_filter: str = "all",
    ) -> tuple[list[dict], int]:
        """Returns (articles_on_page, total_count)."""
        conditions, params = self._build_article_filters(
            source_ids=source_ids,
            search_query=search_query,
            status_filter=status_filter,
        )

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_sql = f"""
            SELECT COUNT(*) FROM articles a
            JOIN sources s ON s.id = a.source_id
            {where}
        """
        total = self._conn.execute(count_sql, params).fetchone()[0]

        offset = (page - 1) * per_page
        data_sql = f"""
            SELECT a.*, s.name AS source_name, s.category, s.language
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            {where}
            ORDER BY COALESCE(a.published_at, a.fetched_at) DESC
            LIMIT ? OFFSET ?
        """
        rows = self._conn.execute(data_sql, [*params, per_page, offset]).fetchall()
        return [dict(r) for r in rows], total

    def get_article_stats(
        self,
        source_ids: Optional[list[int]] = None,
        search_query: Optional[str] = None,
    ) -> dict:
        conditions, params = self._build_article_filters(
            source_ids=source_ids,
            search_query=search_query,
            status_filter="all",
        )
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        row = self._conn.execute(f"""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN COALESCE(a.is_read, 0) = 0 THEN 1 ELSE 0 END), 0) AS unread,
                COALESCE(SUM(CASE WHEN COALESCE(a.is_favorite, 0) = 1 THEN 1 ELSE 0 END), 0) AS favorites,
                COALESCE(SUM(CASE WHEN COALESCE(a.ai_analysis, '') <> '' THEN 1 ELSE 0 END), 0) AS analyzed,
                COALESCE(SUM(CASE WHEN COALESCE(a.ai_analysis, '') = '' THEN 1 ELSE 0 END), 0) AS needs_ai,
                COALESCE(SUM(CASE WHEN COALESCE(a.full_text, '') = '' THEN 1 ELSE 0 END), 0) AS needs_text,
                COALESCE(SUM(CASE WHEN date(COALESCE(a.published_at, a.fetched_at)) = date('now') THEN 1 ELSE 0 END), 0) AS today
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            {where}
        """, params).fetchone()

        top_sources = self._conn.execute(f"""
            SELECT s.name, COUNT(*) AS count
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            {where}
            GROUP BY s.id, s.name
            ORDER BY count DESC, s.name
            LIMIT 3
        """, params).fetchall()

        stats = dict(row) if row else {}
        stats["top_sources"] = [dict(r) for r in top_sources]
        return stats

    def get_articles_for_ai(
        self,
        source_ids: Optional[list[int]] = None,
        search_query: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        conditions, params = self._build_article_filters(
            source_ids=source_ids,
            search_query=search_query,
            status_filter="all",
        )
        conditions.append("COALESCE(a.ai_analysis, '') = ''")
        where = f"WHERE {' AND '.join(conditions)}"

        rows = self._conn.execute(f"""
            SELECT a.*, s.name AS source_name, s.category, s.language
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            {where}
            ORDER BY COALESCE(a.published_at, a.fetched_at) DESC
            LIMIT ?
        """, [*params, limit]).fetchall()
        return [dict(r) for r in rows]

    def get_article_by_id(self, article_id: int) -> Optional[dict]:
        r = self._conn.execute(
            "SELECT a.*, s.name AS source_name, s.category, s.language "
            "FROM articles a JOIN sources s ON s.id = a.source_id WHERE a.id = ?",
            (article_id,)
        ).fetchone()
        return dict(r) if r else None

    def delete_old_articles(self, source_id: int, keep_newest: int) -> None:
        with self._write_lock:
            self._conn.execute("""
                DELETE FROM articles WHERE source_id = ? AND id NOT IN (
                    SELECT id FROM articles WHERE source_id = ?
                    ORDER BY COALESCE(published_at, fetched_at) DESC
                    LIMIT ?
                )
            """, (source_id, source_id, keep_newest))
            self._conn.commit()

    def get_articles_needing_extraction(self, source_id: Optional[int] = None,
                                         limit: int = 50) -> list[dict]:
        """Returns articles that have no full_text yet."""
        q = "SELECT id, url FROM articles WHERE full_text IS NULL"
        params: list = []
        if source_id is not None:
            q += " AND source_id = ?"
            params.append(source_id)
        q += " ORDER BY fetched_at DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self._conn.execute(q, params).fetchall()]

    def cleanup_articles(
        self,
        max_age_days: int,
        max_total_articles: int,
        max_articles_per_source: int,
    ) -> dict:
        """Delete old non-favorite articles and cap total non-favorite storage."""
        deleted_by_age = 0
        deleted_by_total = 0
        deleted_by_source = 0

        with self._write_lock:
            if max_age_days > 0:
                cur = self._conn.execute("""
                    DELETE FROM articles
                    WHERE COALESCE(is_favorite, 0) = 0
                      AND datetime(COALESCE(published_at, fetched_at)) < datetime('now', ?)
                """, (f'-{max_age_days} days',))
                deleted_by_age = max(cur.rowcount, 0)

            if max_articles_per_source > 0:
                source_rows = self._conn.execute("SELECT id FROM sources").fetchall()
                for row in source_rows:
                    cur = self._conn.execute("""
                        DELETE FROM articles
                        WHERE COALESCE(is_favorite, 0) = 0
                          AND source_id = ?
                          AND id NOT IN (
                              SELECT id FROM articles
                              WHERE source_id = ?
                              ORDER BY COALESCE(published_at, fetched_at) DESC
                              LIMIT ?
                          )
                    """, (row['id'], row['id'], max_articles_per_source))
                    deleted_by_source += max(cur.rowcount, 0)

            if max_total_articles > 0:
                cur = self._conn.execute("""
                    DELETE FROM articles
                    WHERE COALESCE(is_favorite, 0) = 0
                      AND id NOT IN (
                          SELECT id FROM articles
                          ORDER BY COALESCE(published_at, fetched_at) DESC
                          LIMIT ?
                      )
                """, (max_total_articles,))
                deleted_by_total = max(cur.rowcount, 0)

            self._conn.commit()

        return {
            'deleted_by_age': deleted_by_age,
            'deleted_by_source': deleted_by_source,
            'deleted_by_total': deleted_by_total,
            'deleted_total': deleted_by_age + deleted_by_source + deleted_by_total,
        }

    def get_source_health(self) -> list[dict]:
        rows = self._conn.execute("""
            SELECT
                s.*,
                COUNT(a.id) AS article_count,
                COALESCE(SUM(CASE WHEN a.id IS NOT NULL AND COALESCE(a.full_text, '') = '' THEN 1 ELSE 0 END), 0) AS missing_text_count,
                MAX(COALESCE(a.published_at, a.fetched_at)) AS newest_article_at,
                MIN(COALESCE(a.published_at, a.fetched_at)) AS oldest_article_at
            FROM sources s
            LEFT JOIN articles a ON a.source_id = s.id
            GROUP BY s.id
            ORDER BY s.enabled DESC, s.category, s.name
        """).fetchall()
        return [self._with_health_score(dict(row)) for row in rows]

    def _with_health_score(self, row: dict) -> dict:
        status = row.get('last_fetch_status') or 'never'
        newest = row.get('newest_article_at') or row.get('last_entry_at')
        hours = self._hours_since(newest)
        row['article_age_hours'] = hours

        if status == 'error':
            row['health'] = 'Error'
            row['health_color'] = '#dc2626'
        elif status == 'never':
            row['health'] = 'Never fetched'
            row['health_color'] = '#6b7280'
        elif not newest:
            row['health'] = 'No articles'
            row['health_color'] = '#d97706'
        elif hours is not None and hours <= 36:
            row['health'] = 'Fresh'
            row['health_color'] = '#059669'
        elif hours is not None and hours <= 168:
            row['health'] = 'Aging'
            row['health_color'] = '#d97706'
        else:
            row['health'] = 'Stale'
            row['health_color'] = '#dc2626'
        return row

    @staticmethod
    def _hours_since(iso_str: Optional[str]) -> Optional[float]:
        if not iso_str:
            return None
        try:
            dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600)
        except Exception:
            return None

    # ── Topic reports ─────────────────────────────────────────────────────

    def get_articles_matching_keywords(
        self,
        keywords: list[str],
        source_ids: Optional[list[int]] = None,
        limit: int = 10,
    ) -> list[dict]:
        clean_keywords = [k.strip() for k in keywords if k.strip()]
        if not clean_keywords:
            return []

        conditions = []
        params: list = []
        if source_ids is not None:
            if not source_ids:
                conditions.append("0")
            else:
                placeholders = ','.join('?' * len(source_ids))
                conditions.append(f"a.source_id IN ({placeholders})")
                params.extend(source_ids)

        keyword_parts = []
        for keyword in clean_keywords:
            keyword_parts.append(
                "(a.title LIKE ? OR COALESCE(a.summary, '') LIKE ? OR "
                "COALESCE(a.full_text, '') LIKE ?)"
            )
            pattern = f"%{keyword}%"
            params.extend([pattern, pattern, pattern])
        conditions.append(f"({' OR '.join(keyword_parts)})")
        where = f"WHERE {' AND '.join(conditions)}"

        rows = self._conn.execute(f"""
            SELECT a.*, s.name AS source_name, s.category, s.language
            FROM articles a
            JOIN sources s ON s.id = a.source_id
            {where}
            ORDER BY COALESCE(a.published_at, a.fetched_at) DESC
            LIMIT ?
        """, [*params, limit]).fetchall()
        return [dict(r) for r in rows]

    def create_topic_report(
        self,
        title: str,
        keywords: list[str],
        language: str,
        article_ids: list[int],
        report: str,
        provider: str,
        model: str,
    ) -> int:
        with self._write_lock:
            cur = self._conn.execute(
                "INSERT INTO topic_reports "
                "(title, keywords, language, article_ids, report, provider, model) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    title,
                    json.dumps(keywords, ensure_ascii=False),
                    language,
                    json.dumps(article_ids),
                    report,
                    provider,
                    model,
                ),
            )
            self._conn.commit()
            return cur.lastrowid

    def get_topic_reports(self, limit: int = 30) -> list[dict]:
        rows = self._conn.execute("""
            SELECT * FROM topic_reports
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [self._decode_topic_report(dict(r)) for r in rows]

    def get_topic_report_by_id(self, report_id: int) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM topic_reports WHERE id = ?", (report_id,)
        ).fetchone()
        return self._decode_topic_report(dict(row)) if row else None

    def _decode_topic_report(self, report: dict) -> dict:
        for key in ("keywords", "article_ids"):
            try:
                report[key] = json.loads(report.get(key) or "[]")
            except Exception:
                report[key] = []
        return report
