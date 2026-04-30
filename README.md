# Global News Reader

A desktop RSS/news reader for collecting international headlines, reading extracted full text, and producing AI-assisted article briefs and topic reports. Built with Python and CustomTkinter.

## Features

- **Multi-source RSS reader**: includes Western, Chinese, Japanese, and Middle Eastern news sources out of the box.
- **Full-text extraction**: fetches article body text with `trafilatura` and a BeautifulSoup fallback.
- **AI article analysis**: per-article summary, keyword extraction, sentiment, and confidence score.
- **AI output language**: choose English, Simplified Chinese, Japanese, Korean, or original-language output for reports and article briefs.
- **Briefing queue**: batch-analyze the latest unprocessed articles in the current source/search scope.
- **Topic reports**: configure keywords and generate persistent Markdown-style intelligence reports from matching articles.
- **Source health panel**: review each source's last fetch time, newest article freshness, failures, stored article count, and missing full-text count.
- **Cleanup rules**: automatically remove old non-favorite articles and cap cache size by age, source, and total count.
- **Read workflow**: unread/saved/analyzed filters, saved articles, mark unread, Markdown export, and source filtering.
- **Local storage**: articles, sources, settings, AI results, source health, and topic reports are stored in SQLite.
- **Auto-refresh**: optional scheduled fetching every 15, 30, or 60 minutes.

## Built-In Sources

| Region | Sources |
|--------|---------|
| Western | BBC World, Reuters, AP News, The Guardian, CNN World |
| Chinese | 人民日报, 新华社 (EN), 澎湃新闻 |
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

Every time after that:

```bat
launch.bat
```

Or directly:

```bash
python main.py
```

## AI Setup

Open **Settings > AI Providers**, enter an API key, and select a model. The app supports Claude, OpenAI, several OpenAI-compatible providers, and a custom compatible endpoint.

In **Settings > Preferences**:

- `AI Report Language`: controls article briefs and topic reports.
- `Auto AI Analysis`: analyzes new articles after refresh.
- `Topic Keywords`: comma, semicolon, or newline-separated keywords for topic reports.
- `Auto Topic Reports`: generates reports after refresh when matching articles exist.

API keys are stored locally in the SQLite database and are only sent to the selected AI provider.

## Source Health

The **Source Health** tab shows:

- fetch status: fresh, aging, stale, error, never fetched, or no articles
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

Cleanup keeps the local database from growing without bound. Favorites are preserved.

Settings:

- `Cleanup Enabled`: master switch.
- `Cleanup on Refresh`: run cleanup after a successful refresh.
- `Max Article Age`: delete non-favorite articles older than this many days.
- `Max Articles/Source`: keep only the newest N articles per source.
- `Max Total Articles`: keep only the newest N articles globally.

You can also run cleanup manually from **Source Health > Cleanup Now**.

## Data Location

All runtime data is stored in `%APPDATA%\GlobalNewsReader\` on Windows:

```text
%APPDATA%\GlobalNewsReader\
├── news.db      # articles, sources, settings, AI analysis, reports, health data
├── app.log      # local logs
├── exports\     # exported article Markdown
└── reports\     # exported topic report Markdown
```

## What Should Not Be Uploaded

The repository should not include local runtime or private files:

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
