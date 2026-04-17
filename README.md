# Global News Reader

A desktop application for browsing and reading international news headlines from major media outlets worldwide. Built with Python.

## Features

- **Multiple news sources** — covers Western, Chinese, Japanese, and Middle Eastern media out of the box
- **Full article text** — fetches complete article content, not just headlines
- **AI analysis** — per-article summary, keyword extraction, and sentiment analysis (supports Claude and OpenAI)
- **Local storage** — articles are saved to a local SQLite database; history persists between sessions
- **Source management** — add any custom RSS feed alongside the built-in sources
- **Search and filter** — full-text search and per-source filtering
- **Auto-refresh** — optional scheduled fetching every 15, 30, or 60 minutes

## Built-in Sources

| Region | Sources |
|--------|---------|
| Western | BBC World, Reuters, AP News, The Guardian, CNN World |
| Chinese | 人民日报, 新华社 (EN), 澎湃新闻 |
| Japanese | NHK World, Asahi Shimbun |
| Middle East | Al Jazeera, Jerusalem Post |

Any RSS feed can be added through the Settings panel.

## Requirements

- Python 3.10 or later
- Windows (tested on Windows 10/11); should also work on macOS and Linux with minor path adjustments

## Setup

**First time:**

```
setup.bat
```

This creates a virtual environment under `venv/` and installs all dependencies. Running it again is safe — it detects an existing environment and only updates packages if needed.

**Every time after that:**

```
launch.bat
```

Or directly:

```
python main.py
```

## Dependencies

All installed automatically by `setup.bat`:

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) — GUI
- [feedparser](https://feedparser.readthedocs.io/) — RSS parsing
- [trafilatura](https://trafilatura.readthedocs.io/) — article text extraction
- [anthropic](https://github.com/anthropics/anthropic-sdk-python) — Claude API
- [openai](https://github.com/openai/openai-python) — OpenAI API
- requests, beautifulsoup4, lxml, Pillow

## AI Analysis Setup

Go to **Settings → AI Providers**, enter your API key, and select a model. Both providers are optional — the app works without them for basic news reading.

- **Claude**: get a key at [console.anthropic.com](https://console.anthropic.com)
- **OpenAI**: get a key at [platform.openai.com](https://platform.openai.com)

API keys are stored locally in your database file (`%APPDATA%\GlobalNewsReader\news.db`) and never transmitted anywhere except the respective API provider.

## Data Location

All data is stored in `%APPDATA%\GlobalNewsReader\` on Windows:

```
%APPDATA%\GlobalNewsReader\
├── news.db      # articles, sources, settings, AI analysis results
└── app.log      # error log
```

## License

MIT
