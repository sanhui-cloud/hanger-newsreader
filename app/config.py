import os
from pathlib import Path

APP_NAME = "Global News Reader"
APP_VERSION = "1.0.0"

# Data stored in %APPDATA%\GlobalNewsReader (Windows) or ~/.GlobalNewsReader (other)
APP_DATA_DIR = Path(os.environ.get('APPDATA', Path.home())) / 'GlobalNewsReader'
DB_PATH = APP_DATA_DIR / 'news.db'
LOG_PATH = APP_DATA_DIR / 'app.log'

CATEGORY_LABELS = {
    'western':   'Western',
    'chinese':   'Chinese',
    'japanese':  'Japanese',
    'middleeast': 'Middle East',
    'custom':    'Custom',
}

CATEGORY_COLORS = {
    'western':   ('#2563eb', '#1d4ed8'),
    'chinese':   ('#dc2626', '#b91c1c'),
    'japanese':  ('#7c3aed', '#6d28d9'),
    'middleeast': ('#059669', '#047857'),
    'custom':    ('#d97706', '#b45309'),
}

DEFAULT_SOURCES: list[dict] = [
    {"name": "BBC World",       "url": "http://feeds.bbci.co.uk/news/world/rss.xml",           "category": "western",    "language": "en"},
    {"name": "Reuters",         "url": "https://feeds.reuters.com/reuters/worldnews",            "category": "western",    "language": "en"},
    {"name": "AP News",         "url": "https://rsshub.app/apnews/topics/apf-topnews",          "category": "western",    "language": "en"},
    {"name": "The Guardian",    "url": "https://www.theguardian.com/world/rss",                  "category": "western",    "language": "en"},
    {"name": "CNN World",       "url": "http://rss.cnn.com/rss/edition_world.rss",               "category": "western",    "language": "en"},
    {"name": "人民日报",         "url": "http://www.people.com.cn/rss/world.xml",                "category": "chinese",    "language": "zh"},
    {"name": "新华社(EN)",       "url": "http://www.xinhuanet.com/english/rss/worldnews.xml",    "category": "chinese",    "language": "en"},
    {"name": "澎湃新闻",         "url": "https://rsshub.app/thepaper/channel/25951",             "category": "chinese",    "language": "zh"},
    {"name": "NHK World",       "url": "https://www3.nhk.or.jp/rss/news/cat0.xml",              "category": "japanese",   "language": "en"},
    {"name": "Asahi Shimbun",   "url": "https://rsshub.app/asahi/english",                      "category": "japanese",   "language": "en"},
    {"name": "Al Jazeera",      "url": "https://www.aljazeera.com/xml/rss/all.xml",              "category": "middleeast", "language": "en"},
    {"name": "Jerusalem Post",  "url": "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",       "category": "middleeast", "language": "en"},
]

DEFAULT_SETTINGS: dict[str, str] = {
    "ai_provider":              "claude",
    "claude_api_key":           "",
    "openai_api_key":           "",
    "claude_model":             "claude-haiku-4-5-20251001",
    "openai_model":             "gpt-4o-mini",
    "auto_refresh_interval":    "0",
    "theme":                    "dark",
    "font_size":                "14",
    "articles_per_page":        "25",
    "extract_full_text":        "1",
    "auto_analyze":             "0",
    "max_articles_per_source":  "100",
}
