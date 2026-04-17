import json
import sqlite3
import threading
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

    def get_articles(
        self,
        source_ids: Optional[list[int]] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> tuple[list[dict], int]:
        """Returns (articles_on_page, total_count)."""
        conditions = []
        params: list = []

        if source_ids is not None:
            placeholders = ','.join('?' * len(source_ids))
            conditions.append(f"a.source_id IN ({placeholders})")
            params.extend(source_ids)

        if search_query:
            conditions.append("(a.title LIKE ? OR a.summary LIKE ?)")
            pattern = f"%{search_query}%"
            params.extend([pattern, pattern])

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
