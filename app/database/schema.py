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
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_published  ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_fetched    ON articles(fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_url        ON articles(url);
"""


def initialize_database(db_path: str) -> None:
    """Create tables, indexes, and seed default data on first run."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.executescript(DDL)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    # Seed default settings only if table is empty
    count = conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
    if count == 0:
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
