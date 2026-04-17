import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk

from app.config import APP_DATA_DIR, DB_PATH
from app.database.schema import initialize_database
from app.database.repository import Repository
from app.feed.pipeline import FetchPipeline
from app.gui.app_window import AppWindow


def main() -> None:
    # Windows high-DPI awareness
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database(str(DB_PATH))

    repo = Repository(str(DB_PATH))

    # Apply saved theme before creating window
    theme = repo.get_setting('theme', 'dark')
    ctk.set_appearance_mode(theme)
    ctk.set_default_color_theme('blue')

    pipeline = FetchPipeline(repo)
    app = AppWindow(repo, pipeline)
    app.mainloop()


if __name__ == '__main__':
    main()
