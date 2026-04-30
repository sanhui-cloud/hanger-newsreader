from typing import Callable
import customtkinter as ctk

from app.utils.date_utils import format_date, relative_time


class SourceHealthPanel(ctk.CTkFrame):
    """Source health, freshness, and cache cleanup controls."""

    def __init__(
        self,
        master,
        on_cleanup: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._on_cleanup = on_cleanup
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_list()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.grid(row=0, column=0, sticky='ew', padx=12, pady=(10, 6))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text='Source Health',
            anchor='w',
            font=ctk.CTkFont(size=16, weight='bold'),
        ).grid(row=0, column=0, sticky='ew')

        self._cleanup_lbl = ctk.CTkLabel(
            header,
            text='Cleanup rules not loaded',
            anchor='e',
            text_color='gray',
            font=ctk.CTkFont(size=11),
        )
        self._cleanup_lbl.grid(row=0, column=1, padx=10, sticky='e')

        ctk.CTkButton(
            header,
            text='Cleanup Now',
            width=112,
            height=30,
            fg_color='transparent',
            border_width=1,
            text_color=('gray20', 'gray80'),
            hover_color=('gray82', 'gray26'),
            command=self._on_cleanup,
        ).grid(row=0, column=2, sticky='e')

    def _build_list(self) -> None:
        self._list = ctk.CTkScrollableFrame(self)
        self._list.grid(row=1, column=0, sticky='nsew', padx=8, pady=(0, 8))
        self._list.columnconfigure(0, weight=1)

    def display(self, sources: list[dict], settings: dict) -> None:
        for child in self._list.winfo_children():
            child.destroy()

        cleanup_state = 'on' if settings.get('cleanup_enabled', '1') == '1' else 'off'
        age = settings.get('max_article_age_days', '90')
        total = settings.get('max_total_articles', '2000')
        per_source = settings.get('max_articles_per_source', '100')
        self._cleanup_lbl.configure(
            text=f'Cleanup {cleanup_state} | age {age}d | total {total} | per source {per_source}'
        )

        if not sources:
            ctk.CTkLabel(
                self._list,
                text='No sources configured.',
                text_color='gray',
            ).grid(row=0, column=0, padx=10, pady=20)
            return

        for row, source in enumerate(sources):
            self._build_source_row(row, source)

    def _build_source_row(self, row: int, source: dict) -> None:
        card = ctk.CTkFrame(
            self._list,
            corner_radius=8,
            border_width=1,
            border_color=('#d7dde5', '#2b333c'),
            fg_color=('#ffffff', '#171b20'),
        )
        card.grid(row=row, column=0, sticky='ew', padx=4, pady=4)
        card.columnconfigure(1, weight=1)
        card.columnconfigure(2, weight=1)

        status = ctk.CTkLabel(
            card,
            text=source.get('health', 'Unknown'),
            width=96,
            fg_color=source.get('health_color', '#6b7280'),
            text_color='white',
            corner_radius=4,
            font=ctk.CTkFont(size=11, weight='bold'),
        )
        status.grid(row=0, column=0, padx=(8, 8), pady=(8, 2), sticky='nw')

        title = ctk.CTkLabel(
            card,
            text=source.get('name', 'Unknown source'),
            anchor='w',
            font=ctk.CTkFont(size=13, weight='bold'),
        )
        title.grid(row=0, column=1, columnspan=2, padx=(0, 8), pady=(8, 2), sticky='ew')

        counts = (
            f"{source.get('article_count', 0)} stored | "
            f"{source.get('missing_text_count', 0)} missing text | "
            f"{source.get('last_new_count', 0)} new last fetch"
        )
        ctk.CTkLabel(
            card,
            text=counts,
            anchor='w',
            text_color='gray',
            font=ctk.CTkFont(size=11),
        ).grid(row=1, column=1, columnspan=2, padx=(0, 8), sticky='ew')

        newest = source.get('newest_article_at') or source.get('last_entry_at')
        freshness = relative_time(newest) if newest else 'no article time'
        if source.get('article_age_hours') is not None:
            freshness += f" ({source['article_age_hours']:.1f}h)"

        left_meta = (
            f"Last fetch: {format_date(source.get('last_fetched_at')) or 'never'}"
        )
        right_meta = f"Newest article: {freshness}"

        ctk.CTkLabel(
            card,
            text=left_meta,
            anchor='w',
            text_color=('gray35', 'gray68'),
            font=ctk.CTkFont(size=11),
        ).grid(row=2, column=1, padx=(0, 8), pady=(4, 8), sticky='ew')

        ctk.CTkLabel(
            card,
            text=right_meta,
            anchor='w',
            text_color=('gray35', 'gray68'),
            font=ctk.CTkFont(size=11),
        ).grid(row=2, column=2, padx=(0, 8), pady=(4, 8), sticky='ew')

        if source.get('last_error'):
            ctk.CTkLabel(
                card,
                text=f"Error: {source.get('last_error', '')}",
                anchor='w',
                justify='left',
                wraplength=600,
                text_color='#dc2626',
                font=ctk.CTkFont(size=10),
            ).grid(row=3, column=1, columnspan=2, padx=(0, 8), pady=(0, 8), sticky='ew')
