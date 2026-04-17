from typing import Callable
import customtkinter as ctk
from app.utils.date_utils import relative_time
from app.gui.widgets.category_tag import CategoryTag


class ArticleCard(ctk.CTkFrame):
    """One article row: category tag + title + source/date + AI badge."""

    def __init__(self, master, article: dict,
                 on_click: Callable[[dict], None], **kwargs):
        super().__init__(master, cursor='hand2', **kwargs)
        self._article = article
        self._on_click = on_click
        self._selected = False

        self.columnconfigure(1, weight=1)
        self._build()

        for w in self.winfo_children() + [self]:
            w.bind('<Button-1>', self._click)
            w.bind('<Enter>', self._enter)
            w.bind('<Leave>', self._leave)

        self.bind('<Configure>', self._on_resize)

    def _build(self) -> None:
        a = self._article

        # Row 0: category tag + title
        tag = CategoryTag.for_category(self, a.get('category', ''))
        tag.grid(row=0, column=0, padx=(6, 4), pady=(6, 2), sticky='nw')

        title = a.get('title', '(no title)')
        self._title_lbl = ctk.CTkLabel(
            self, text=title, anchor='w', justify='left',
            wraplength=300,
            font=ctk.CTkFont(size=13, weight='bold'),
        )
        self._title_lbl.grid(row=0, column=1, padx=(2, 6), pady=(6, 2), sticky='ew')

        # Row 1: source name + date + AI badge
        meta_frame = ctk.CTkFrame(self, fg_color='transparent')
        meta_frame.grid(row=1, column=0, columnspan=2, padx=6, pady=(0, 6), sticky='ew')
        meta_frame.columnconfigure(0, weight=1)

        source = a.get('source_name', '')
        date_str = relative_time(a.get('published_at'))
        meta_text = f"{source}  ·  {date_str}" if date_str else source
        ctk.CTkLabel(
            meta_frame, text=meta_text, anchor='w',
            text_color='gray', font=ctk.CTkFont(size=11),
        ).grid(row=0, column=0, sticky='ew')

        if a.get('ai_analysis'):
            ctk.CTkLabel(
                meta_frame, text='AI✓', text_color='#10b981',
                font=ctk.CTkFont(size=10, weight='bold'),
            ).grid(row=0, column=1, padx=(4, 0))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.configure(
            fg_color=('lightblue', '#1a3a5c') if selected
            else ('gray92', 'gray17')
        )

    def _click(self, _=None) -> None:
        self._on_click(self._article)

    def _enter(self, _=None) -> None:
        if not self._selected:
            self.configure(fg_color=('gray85', 'gray25'))

    def _leave(self, _=None) -> None:
        if not self._selected:
            self.configure(fg_color=('gray92', 'gray17'))

    def update_wraplength(self, width: int) -> None:
        self._title_lbl.configure(wraplength=max(100, width - 80))

    def _on_resize(self, event) -> None:
        self.update_wraplength(event.width)
