import math
from typing import Callable, Optional
import customtkinter as ctk
from app.gui.widgets.article_card import ArticleCard


class ArticleList(ctk.CTkFrame):
    """Center pane: paginated scrollable article cards."""

    def __init__(self, master, on_select: Callable[[dict], None], **kwargs):
        super().__init__(master, **kwargs)
        self._on_select = on_select
        self._articles: list[dict] = []
        self._cards: list[ArticleCard] = []
        self._selected_id: Optional[int] = None
        self._current_page = 1
        self._total_pages = 1
        self._per_page = 25
        self._on_page_change: Optional[Callable[[int], None]] = None

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Scrollable area for cards
        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.grid(row=0, column=0, sticky='nsew')
        self._scroll.columnconfigure(0, weight=1)

        # Pagination bar
        self._build_pagination_bar()

        self._show_empty('No articles loaded. Click Refresh to fetch news.')

    def _build_pagination_bar(self) -> None:
        bar = ctk.CTkFrame(self, height=40, fg_color=('gray88', 'gray20'))
        bar.grid(row=1, column=0, sticky='ew')
        bar.columnconfigure(1, weight=1)

        self._prev_btn = ctk.CTkButton(
            bar, text='< Prev', width=72, height=28,
            command=self._prev_page, state='disabled',
        )
        self._prev_btn.grid(row=0, column=0, padx=(8, 4), pady=6)

        self._page_lbl = ctk.CTkLabel(bar, text='Page 1 of 1', anchor='center')
        self._page_lbl.grid(row=0, column=1, sticky='ew')

        self._next_btn = ctk.CTkButton(
            bar, text='Next >', width=72, height=28,
            command=self._next_page, state='disabled',
        )
        self._next_btn.grid(row=0, column=2, padx=(4, 4), pady=6)

        self._per_page_menu = ctk.CTkOptionMenu(
            bar, values=['15', '25', '50', '100'], width=72,
            command=self._on_per_page_change,
        )
        self._per_page_menu.set('25')
        self._per_page_menu.grid(row=0, column=3, padx=(4, 8), pady=6)

    def display(self, articles: list[dict], total_count: int, page: int,
                per_page: int, on_page_change: Callable[[int], None]) -> None:
        """Render one page of articles."""
        self._articles = articles
        self._current_page = page
        self._per_page = per_page
        self._total_pages = max(1, math.ceil(total_count / per_page))
        self._on_page_change = on_page_change

        # Clear existing cards
        for card in self._cards:
            card.destroy()
        self._cards.clear()
        self._selected_id = None

        # Remove empty label if present
        for child in self._scroll.winfo_children():
            child.destroy()

        if not articles:
            self._show_empty('No articles match current filters.')
            return

        for i, art in enumerate(articles):
            card = ArticleCard(
                self._scroll, art,
                on_click=self._card_clicked,
            )
            card.grid(row=i, column=0, padx=4, pady=2, sticky='ew')
            self._cards.append(card)

        self._update_pagination()

    def _show_empty(self, msg: str) -> None:
        for child in self._scroll.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self._scroll, text=msg, text_color='gray',
            wraplength=300,
        ).grid(row=0, column=0, pady=30, padx=20)

    def _update_pagination(self) -> None:
        self._page_lbl.configure(
            text=f'Page {self._current_page} of {self._total_pages}'
        )
        self._prev_btn.configure(
            state='normal' if self._current_page > 1 else 'disabled'
        )
        self._next_btn.configure(
            state='normal' if self._current_page < self._total_pages else 'disabled'
        )

    def _card_clicked(self, article: dict) -> None:
        # Update selection state
        for card in self._cards:
            card.set_selected(card._article.get('id') == article.get('id'))
        self._selected_id = article.get('id')
        self._on_select(article)

    def _prev_page(self) -> None:
        if self._on_page_change and self._current_page > 1:
            self._on_page_change(self._current_page - 1)

    def _next_page(self) -> None:
        if self._on_page_change and self._current_page < self._total_pages:
            self._on_page_change(self._current_page + 1)

    def _on_per_page_change(self, value: str) -> None:
        self._per_page = int(value)
        if self._on_page_change:
            self._on_page_change(1)

    def get_per_page(self) -> int:
        return self._per_page

    def mark_article_analyzed(self, article_id: int) -> None:
        """Mark the card's article as analyzed (shows AI badge on next display)."""
        for card in self._cards:
            if card._article.get('id') == article_id:
                card._article['ai_analysis'] = 'updated'
                break
