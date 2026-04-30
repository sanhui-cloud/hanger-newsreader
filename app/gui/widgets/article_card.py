from typing import Callable
import customtkinter as ctk

from app.gui.widgets.category_tag import CategoryTag
from app.utils.date_utils import relative_time


class ArticleCard(ctk.CTkFrame):
    """One article row with read state, preview text, and useful badges."""

    def __init__(self, master, article: dict,
                 on_click: Callable[[dict], None], **kwargs):
        super().__init__(master, cursor='hand2', **kwargs)
        self._article = article
        self._on_click = on_click
        self._selected = False

        self.columnconfigure(2, weight=1)
        self._build()

        self._bind_tree(self)

        self.bind('<Configure>', self._on_resize)

    def _build(self) -> None:
        a = self._article
        self.configure(
            corner_radius=8,
            border_width=1,
            border_color=('#d7dde5', '#2b333c'),
            fg_color=('#ffffff', '#171b20'),
        )

        unread = not bool(a.get('is_read', 0))
        self._unread_lbl = ctk.CTkLabel(
            self,
            text='●' if unread else '',
            width=14,
            text_color='#0ea5e9',
            font=ctk.CTkFont(size=12, weight='bold'),
        )
        self._unread_lbl.grid(row=0, column=0, rowspan=3, padx=(8, 0), pady=(8, 6), sticky='n')

        tag = CategoryTag.for_category(self, a.get('category', ''))
        tag.grid(row=0, column=1, padx=(6, 6), pady=(8, 3), sticky='nw')

        title = a.get('title', '(no title)')
        self._title_lbl = ctk.CTkLabel(
            self,
            text=title,
            anchor='w',
            justify='left',
            wraplength=320,
            font=ctk.CTkFont(size=13, weight='bold' if unread else 'normal'),
            text_color=('#0f172a', '#f8fafc') if unread else ('#334155', '#cbd5e1'),
        )
        self._title_lbl.grid(row=0, column=2, padx=(0, 8), pady=(8, 2), sticky='ew')

        if a.get('is_favorite'):
            ctk.CTkLabel(
                self,
                text='Saved',
                text_color='#d97706',
                font=ctk.CTkFont(size=10, weight='bold'),
            ).grid(row=0, column=3, padx=(0, 8), pady=(8, 2), sticky='ne')

        snippet = self._snippet(a)
        if snippet:
            self._snippet_lbl = ctk.CTkLabel(
                self,
                text=snippet,
                anchor='w',
                justify='left',
                wraplength=420,
                text_color=('gray35', 'gray68'),
                font=ctk.CTkFont(size=11),
            )
            self._snippet_lbl.grid(
                row=1,
                column=1,
                columnspan=3,
                padx=(6, 8),
                pady=(0, 4),
                sticky='ew',
            )

        meta_frame = ctk.CTkFrame(self, fg_color='transparent')
        meta_frame.grid(row=2, column=1, columnspan=3, padx=(6, 8), pady=(0, 8), sticky='ew')
        meta_frame.columnconfigure(0, weight=1)

        source = a.get('source_name', '')
        date_str = relative_time(a.get('published_at'))
        meta_text = f"{source}  ·  {date_str}" if date_str else source
        ctk.CTkLabel(
            meta_frame,
            text=meta_text,
            anchor='w',
            text_color='gray',
            font=ctk.CTkFont(size=11),
        ).grid(row=0, column=0, sticky='ew')

        if a.get('full_text'):
            ctk.CTkLabel(
                meta_frame,
                text='Text',
                text_color='#0891b2',
                font=ctk.CTkFont(size=10, weight='bold'),
            ).grid(row=0, column=1, padx=(4, 0))

        if a.get('ai_analysis'):
            ctk.CTkLabel(
                meta_frame,
                text='AI',
                text_color='#10b981',
                font=ctk.CTkFont(size=10, weight='bold'),
            ).grid(row=0, column=2, padx=(6, 0))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.configure(
            fg_color=('#dbeafe', '#12304d') if selected
            else ('#ffffff', '#171b20')
        )

    def set_read(self, is_read: bool) -> None:
        self._article['is_read'] = int(is_read)
        self._unread_lbl.configure(text='' if is_read else '●')
        self._title_lbl.configure(
            font=ctk.CTkFont(size=13, weight='normal' if is_read else 'bold'),
            text_color=('#334155', '#cbd5e1') if is_read else ('#0f172a', '#f8fafc'),
        )

    def _click(self, _=None) -> None:
        self._on_click(self._article)

    def _enter(self, _=None) -> None:
        if not self._selected:
            self.configure(fg_color=('#eef4fb', '#222a33'))

    def _leave(self, _=None) -> None:
        if not self._selected:
            self.configure(fg_color=('#ffffff', '#171b20'))

    def update_wraplength(self, width: int) -> None:
        self._title_lbl.configure(wraplength=max(120, width - 150))
        if hasattr(self, '_snippet_lbl'):
            self._snippet_lbl.configure(wraplength=max(120, width - 70))

    def _on_resize(self, event) -> None:
        self.update_wraplength(event.width)

    def _bind_tree(self, widget) -> None:
        widget.bind('<Button-1>', self._click)
        widget.bind('<Enter>', self._enter)
        widget.bind('<Leave>', self._leave)
        for child in widget.winfo_children():
            self._bind_tree(child)

    @staticmethod
    def _snippet(article: dict) -> str:
        raw = article.get('summary') or article.get('full_text') or ''
        text = ' '.join(raw.split())
        if len(text) > 180:
            return text[:177].rstrip() + '...'
        return text
