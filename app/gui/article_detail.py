import json
import webbrowser
from typing import Optional, Callable
import customtkinter as ctk
from app.utils.date_utils import format_date
from app.gui.widgets.category_tag import CategoryTag


class ArticleDetail(ctk.CTkFrame):
    """Right pane: article metadata, full text tab, AI analysis tab."""

    def __init__(self, master, on_extract_text: Callable[[dict], None],
                 on_analyze: Callable[[dict], None], **kwargs):
        super().__init__(master, **kwargs)
        self._on_extract = on_extract_text
        self._on_analyze = on_analyze
        self._current_article: Optional[dict] = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_tabs()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 0))
        header.columnconfigure(0, weight=1)

        self._title_lbl = ctk.CTkLabel(
            header,
            text='Select an article to read',
            anchor='w', justify='left',
            wraplength=500,
            font=ctk.CTkFont(size=15, weight='bold'),
        )
        self._title_lbl.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 6))

        self._meta_lbl = ctk.CTkLabel(
            header, text='', anchor='w', text_color='gray',
            font=ctk.CTkFont(size=12),
        )
        self._meta_lbl.grid(row=1, column=0, sticky='ew')

        self._open_btn = ctk.CTkButton(
            header, text='Open in Browser', width=130, height=26,
            font=ctk.CTkFont(size=11),
            command=self._open_browser,
            state='disabled',
        )
        self._open_btn.grid(row=1, column=1, padx=(8, 0))

        sep = ctk.CTkFrame(header, height=1, fg_color=('gray70', 'gray40'))
        sep.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(8, 0))

    def _build_tabs(self) -> None:
        self._tabview = ctk.CTkTabview(self)
        self._tabview.grid(row=1, column=0, sticky='nsew', padx=6, pady=6)

        # Full Text tab
        self._tabview.add('Full Text')
        ft_frame = self._tabview.tab('Full Text')
        ft_frame.rowconfigure(0, weight=1)
        ft_frame.columnconfigure(0, weight=1)

        self._text_box = ctk.CTkTextbox(
            ft_frame, state='disabled', wrap='word',
            font=ctk.CTkFont(family='Microsoft YaHei', size=13),
        )
        self._text_box.grid(row=0, column=0, sticky='nsew')

        self._extract_btn = ctk.CTkButton(
            ft_frame, text='Extract Full Text', height=30,
            command=self._do_extract, state='disabled',
        )
        self._extract_btn.grid(row=1, column=0, pady=(4, 0), padx=4, sticky='ew')

        # AI Analysis tab
        self._tabview.add('AI Analysis')
        ai_frame = self._tabview.tab('AI Analysis')
        ai_frame.columnconfigure(0, weight=1)
        self._build_ai_tab(ai_frame)

    def _build_ai_tab(self, parent: ctk.CTkFrame) -> None:
        self._ai_placeholder = ctk.CTkLabel(
            parent, text='No analysis yet.\nSelect an article and click "✦ AI Analyze".',
            text_color='gray', justify='center',
        )
        self._ai_placeholder.grid(row=0, column=0, pady=30)

        self._ai_content = ctk.CTkFrame(parent, fg_color='transparent')
        self._ai_content.columnconfigure(0, weight=1)
        # Hidden initially; shown when analysis exists

        ctk.CTkLabel(self._ai_content, text='Summary', anchor='w',
                      font=ctk.CTkFont(size=12, weight='bold')).grid(
            row=0, column=0, sticky='ew', padx=6, pady=(8, 2))
        self._ai_summary = ctk.CTkTextbox(self._ai_content, height=80, state='disabled',
                                           wrap='word', font=ctk.CTkFont(size=12))
        self._ai_summary.grid(row=1, column=0, sticky='ew', padx=6)

        ctk.CTkLabel(self._ai_content, text='Keywords', anchor='w',
                      font=ctk.CTkFont(size=12, weight='bold')).grid(
            row=2, column=0, sticky='ew', padx=6, pady=(10, 2))
        self._ai_keywords_frame = ctk.CTkFrame(self._ai_content, fg_color='transparent')
        self._ai_keywords_frame.grid(row=3, column=0, sticky='ew', padx=6)

        ctk.CTkLabel(self._ai_content, text='Sentiment', anchor='w',
                      font=ctk.CTkFont(size=12, weight='bold')).grid(
            row=4, column=0, sticky='ew', padx=6, pady=(10, 2))
        self._ai_sentiment = ctk.CTkLabel(self._ai_content, text='', anchor='w',
                                           font=ctk.CTkFont(size=13))
        self._ai_sentiment.grid(row=5, column=0, sticky='ew', padx=6)

        self._ai_meta = ctk.CTkLabel(self._ai_content, text='', anchor='w',
                                      text_color='gray', font=ctk.CTkFont(size=10))
        self._ai_meta.grid(row=6, column=0, sticky='ew', padx=6, pady=(8, 6))

        ctk.CTkButton(
            self._ai_content, text='Re-Analyze', height=28,
            command=self._do_analyze,
        ).grid(row=7, column=0, padx=6, pady=(4, 8), sticky='ew')

    def display_article(self, article: dict) -> None:
        self._current_article = article

        self._title_lbl.configure(text=article.get('title', '(no title)'))
        meta_parts = [
            article.get('source_name', ''),
            format_date(article.get('published_at')),
            article.get('language', '').upper(),
        ]
        self._meta_lbl.configure(text='  ·  '.join(p for p in meta_parts if p))
        self._open_btn.configure(state='normal')

        # Full text tab
        full_text = article.get('full_text') or ''
        if full_text:
            self._set_text(full_text)
            self._extract_btn.configure(state='disabled', text='Full text loaded')
        else:
            summary = article.get('summary') or ''
            self._set_text(summary + '\n\n[Full text not yet extracted]' if summary
                           else '[Full text not available]')
            self._extract_btn.configure(state='normal', text='Extract Full Text')

        # AI tab
        ai_json = article.get('ai_analysis')
        if ai_json:
            try:
                self._show_analysis(json.loads(ai_json))
            except Exception:
                self._show_analysis_placeholder()
        else:
            self._show_analysis_placeholder()

    def display_loading(self) -> None:
        self._set_text('Loading...')

    def _show_analysis_placeholder(self) -> None:
        self._ai_content.grid_remove()
        self._ai_placeholder.grid(row=0, column=0, pady=30)

    def _show_analysis(self, data: dict) -> None:
        self._ai_placeholder.grid_remove()
        self._ai_content.grid(row=0, column=0, sticky='nsew', padx=4)

        # Summary
        self._ai_summary.configure(state='normal')
        self._ai_summary.delete('1.0', 'end')
        self._ai_summary.insert('1.0', data.get('summary', ''))
        self._ai_summary.configure(state='disabled')

        # Keywords
        for child in self._ai_keywords_frame.winfo_children():
            child.destroy()
        for kw in data.get('keywords', []):
            CategoryTag(self._ai_keywords_frame, text=kw).pack(side='left', padx=2, pady=2)

        # Sentiment
        sentiment = data.get('sentiment', 'neutral')
        conf = data.get('confidence', 0)
        sent_tag = CategoryTag.for_sentiment(self._ai_sentiment.master, sentiment)
        sent_tag.pack_forget()
        self._ai_sentiment.configure(
            text=f'{sentiment.title()}  (confidence: {conf:.0%})'
        )

        # Meta
        provider = data.get('provider', '')
        model = data.get('model', '')
        analyzed_at = data.get('analyzed_at', '')[:16].replace('T', ' ')
        self._ai_meta.configure(text=f'Analyzed by {provider}/{model}  ·  {analyzed_at}')

    def _set_text(self, text: str) -> None:
        self._text_box.configure(state='normal')
        self._text_box.delete('1.0', 'end')
        self._text_box.insert('1.0', text)
        self._text_box.configure(state='disabled')
        self._text_box.yview_moveto(0)

    def _open_browser(self) -> None:
        if self._current_article:
            url = self._current_article.get('url', '')
            if url:
                webbrowser.open(url)

    def _do_extract(self) -> None:
        if self._current_article:
            self._extract_btn.configure(state='disabled', text='Extracting...')
            self._on_extract(self._current_article)

    def _do_analyze(self) -> None:
        if self._current_article:
            self._on_analyze(self._current_article)

    def update_full_text(self, text: str) -> None:
        self._set_text(text)
        self._extract_btn.configure(state='disabled', text='Full text loaded')
        if self._current_article:
            self._current_article['full_text'] = text

    def update_analysis(self, analysis_json: str) -> None:
        if self._current_article:
            self._current_article['ai_analysis'] = analysis_json
        try:
            self._show_analysis(json.loads(analysis_json))
        except Exception:
            pass
