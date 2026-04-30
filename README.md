# Global News Reader

A desktop RSS/news workbench for collecting international headlines, reading extracted article text, and producing AI-assisted article briefs and topic reports. Built with Python and CustomTkinter.

## Features

- **Multi-source RSS reader**: includes Western, Chinese, Japanese, and Middle Eastern news feeds out of the box.
- **Full-text extraction**: extracts article bodies with `trafilatura`; if extraction fails, the app tries a BeautifulSoup-based fallback.
- **AI article analysis**: generates per-article summaries, keywords, sentiment labels, and confidence scores.
- **AI output language**: supports English, Simplified Chinese, Japanese, Korean, or original-language output for article briefs and topic reports.
- **Briefing queue**: batch-analyzes the newest unprocessed articles in the current source/search scope.
- **Topic reports**: watches configured keywords and generates persistent Markdown-style reports from matching articles.
- **Source health panel**: shows each feed's last fetch time, newest article freshness, failure state, stored article count, and missing full-text count.
- **Cleanup rules**: removes old non-favorite articles and caps the local article cache by age, per-source count, and global count.
- **Reading workflow**: unread/saved/analyzed filters, saved articles, mark unread, Markdown export, source filtering, and full-text reading.
- **Local storage**: stores articles, sources, settings, AI results, source health, and topic reports in SQLite.
- **Auto-refresh**: optional scheduled fetching every 15, 30, or 60 minutes.

## Built-In Sources

| Region | Sources |
|--------|---------|
| Western | BBC World, Reuters, AP News, The Guardian, CNN World |
| Chinese | People's Daily, Xinhua English, The Paper |
| Japanese | NHK World, Asahi Shimbun |
| Middle East | Al Jazeera, Jerusalem Post |

Any RSS feed can be added through the Settings panel.

## Requirements

- Python 3.10 or later
- Windows 10/11 tested; macOS and Linux may need small path or launcher adjustments

## Setup

First time:

```bat
setup.bat
```

This creates `venv/` and installs the required Python packages.

Every time after that:

```bat
launch.bat
```

Or directly:

```bash
python main.py
```

## AI Setup

Basic RSS reading works without an API key. AI features require a configured provider.

Open **Settings > AI Providers**, enter an API key, and select a model. The app supports Claude, OpenAI, several OpenAI-compatible providers, and a custom OpenAI-compatible endpoint.

In **Settings > Preferences**:

- `AI Report Language`: controls the output language for article briefs and topic reports.
- `Auto AI Analysis`: analyzes new articles after refresh.
- `Topic Keywords`: comma, semicolon, or newline-separated keywords for topic reports.
- `Auto Topic Reports`: generates reports after refresh when matching articles exist.

API keys are stored locally in the SQLite database and are only sent to the selected AI provider.

## Source Health

The **Source Health** tab shows:

- fetch status: Fresh, Aging, Stale, Error, Never fetched, or No articles
- last fetch time and newest article time
- newest article age in hours
- number of stored articles
- number of articles missing extracted full text
- new articles found in the most recent fetch
- last fetch error, when present

Health is based on the newest stored article or the newest article timestamp returned by the RSS feed:

- Fresh: newest article within 36 hours
- Aging: newest article within 7 days
- Stale: newest article older than 7 days
- Error: the last fetch failed

## Cleanup Rules

Cleanup keeps the local database from growing without bound. Favorite articles are preserved.

Settings:

- `Cleanup Enabled`: master switch for automatic and manual cleanup.
- `Cleanup on Refresh`: run cleanup after refresh.
- `Max Article Age`: delete non-favorite articles older than this many days.
- `Max Articles/Source`: keep only the newest N articles per source.
- `Max Total Articles`: keep only the newest N articles globally.

When both `Cleanup Enabled` and `Cleanup on Refresh` are on, the cleanup rules run after each refresh. You can also run the same rules manually from **Source Health > Cleanup Now**.

## Data Location

All runtime data is stored in `%APPDATA%\GlobalNewsReader\` on Windows:

```text
%APPDATA%\GlobalNewsReader\
+-- news.db      # articles, sources, settings, AI analysis, reports, health data
+-- app.log      # local logs
+-- exports\     # exported article Markdown
`-- reports\     # exported topic report Markdown
```

## What Should Not Be Uploaded

The repository should not include private, runtime, or generated files:

- `venv/`
- `.env`
- `.claude/`
- `__pycache__/`, `*.pyc`, `*.pyo`
- local SQLite databases: `*.db`, `*.sqlite`, `*.db-shm`, `*.db-wal`
- logs: `*.log`
- generated exports: `exports/`, `reports/`
- local validation screenshots: `assets/ui_*.png`
- internal or scratch notes: `docs/`
- IDE folders: `.idea/`, `.vscode/`

These are covered by `.gitignore`.

## Dependencies

Installed by `setup.bat`:

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) for GUI
- [feedparser](https://feedparser.readthedocs.io/) for RSS parsing
- [trafilatura](https://trafilatura.readthedocs.io/) for article extraction
- [anthropic](https://github.com/anthropics/anthropic-sdk-python) for Claude
- [openai](https://github.com/openai/openai-python) for OpenAI and compatible APIs
- requests, beautifulsoup4, lxml, Pillow

## License

MIT
