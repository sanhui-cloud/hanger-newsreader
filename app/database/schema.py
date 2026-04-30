import sqlite3
from app.config import DEFAULT_SOURCES, DEFAULT_SETTINGS


DDL = """
CREATE TABLE IF NOT EXISTS sources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    url         TEXT    NOT NULL UNIQUE,
    category    TEXT    NOT NULL,
    language    TEXT    NOT NULL DEFAULT 'en',
    enabled     INTEGER NOT NULL DEFAULT 1,
    custom      INTEGER NOT NULL DEFAULT 0,
    last_fetched_at TEXT,
    last_success_at TEXT,
    last_error TEXT,
    last_new_count INTEGER NOT NULL DEFAULT 0,
    last_entry_at TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_fetch_status TEXT NOT NULL DEFAULT 'never',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS articles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id    INTEGER NOT NULL,
    title        TEXT    NOT NULL,
    url          TEXT    NOT NULL UNIQUE,
    summary      TEXT,
    full_text    TEXT,
    published_at TEXT,
    fetched_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    ai_analysis  TEXT,
    is_read      INTEGER NOT NULL DEFAULT 0,
    is_favorite  INTEGER NOT NULL DEFAULT 0,
    read_at      TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topic_reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    keywords    TEXT    NOT NULL,
    language    TEXT    NOT NULL,
    article_ids TEXT    NOT NULL,
    report      TEXT    NOT NULL,
    provider    TEXT,
    model       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_published  ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_fetched    ON articles(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_url        ON articles(url);
CREATE INDEX IF NOT EXISTS idx_topic_reports_created ON topic_reports(created_at DESC);
"""


def _ensure_article_columns(conn: sqlite3.Connection) -> None:
    """Apply lightweight migrations for existing local databases."""
    rows = conn.execute("PRAGMA table_info(articles)").fetchall()
    existing = {row[1] for row in rows}
    migrations = {
        "is_read": "ALTER TABLE articles ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0",
        "is_favorite": "ALTER TABLE articles ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0",
        "read_at": "ALTER TABLE articles ADD COLUMN read_at TEXT",
    }
    for column, ddl in migrations.items():
        if column not in existing:
            conn.execute(ddl)


def _ensure_source_columns(conn: sqlite3.Connection) -> None:
    """Apply lightweight source-health migrations for existing databases."""
    rows = conn.execute("PRAGMA table_info(sources)").fetchall()
    existing = {row[1] for row in rows}
    migrations = {
        "last_fetched_at": "ALTER TABLE sources ADD COLUMN last_fetched_at TEXT",
        "last_success_at": "ALTER TABLE sources ADD COLUMN last_success_at TEXT",
        "last_error": "ALTER TABLE sources ADD COLUMN last_error TEXT",
        "last_new_count": "ALTER TABLE sources ADD COLUMN last_new_count INTEGER NOT NULL DEFAULT 0",
        "last_entry_at": "ALTER TABLE sources ADD COLUMN last_entry_at TEXT",
        "consecutive_failures": "ALTER TABLE sources ADD COLUMN consecutive_failures INTEGER NOT NULL DEFAULT 0",
        "last_fetch_status": "ALTER TABLE sources ADD COLUMN last_fetch_status TEXT NOT NULL DEFAULT 'never'",
    }
    for column, ddl in migrations.items():
        if column not in existing:
            conn.execute(ddl)


def initialize_database(db_path: str) -> None:
    """Create tables, indexes, and seed default data on first run."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.executescript(DDL)
    _ensure_source_columns(conn)
    _ensure_article_columns(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_read ON articles(is_read, fetched_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_favorite ON articles(is_favorite, fetched_at DESC)")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    # Seed any missing settings without overwriting local user choices.
    conn.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        list(DEFAULT_SETTINGS.items())
    )

    # Seed default sources only if table is empty
    count = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT OR IGNORE INTO sources (name, url, category, language) VALUES (?, ?, ?, ?)",
            [(s['name'], s['url'], s['category'], s['language']) for s in DEFAULT_SOURCES]
        )

    conn.commit()
    conn.close()
