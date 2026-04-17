import customtkinter as ctk
from app.config import CATEGORY_LABELS


class SettingsDialog(ctk.CTkToplevel):
    """Modal settings dialog: AI providers, sources, preferences."""

    def __init__(self, master, repository, on_save=None):
        super().__init__(master)
        self.title('Settings')
        self.geometry('720x540')
        self.resizable(True, True)
        self.minsize(620, 480)
        self.grab_set()
        self._repo = repository
        self._on_save = on_save
        self._settings = repository.get_all_settings()

        self._tabview = ctk.CTkTabview(self)
        self._tabview.pack(fill='both', expand=True, padx=12, pady=12)

        self._tabview.add('AI Providers')
        self._tabview.add('Sources')
        self._tabview.add('Preferences')

        self._build_ai_tab(self._tabview.tab('AI Providers'))
        self._build_sources_tab(self._tabview.tab('Sources'))
        self._build_prefs_tab(self._tabview.tab('Preferences'))

        btn_row = ctk.CTkFrame(self, fg_color='transparent')
        btn_row.pack(fill='x', padx=12, pady=(0, 12))
        ctk.CTkButton(btn_row, text='Save', width=100,
                       command=self._save).pack(side='right', padx=(8, 0))
        ctk.CTkButton(btn_row, text='Cancel', width=100, fg_color='gray',
                       command=self.destroy).pack(side='right')

    # ── AI Providers tab ─────────────────────────────────────────────────

    def _build_ai_tab(self, parent: ctk.CTkFrame) -> None:
        parent.columnconfigure(1, weight=1)

        self._provider_var = ctk.StringVar(
            value=self._settings.get('ai_provider', 'claude').title()
        )
        r = 0
        ctk.CTkLabel(parent, text='Active Provider:', anchor='w').grid(
            row=r, column=0, padx=8, pady=8, sticky='w')
        ctk.CTkSegmentedButton(
            parent, values=['Claude', 'OpenAI'], variable=self._provider_var,
        ).grid(row=r, column=1, padx=8, pady=8, sticky='w')

        def _add_key_row(label, key, placeholder, row):
            ctk.CTkLabel(parent, text=label, anchor='w').grid(
                row=row, column=0, padx=8, pady=4, sticky='w')
            var = ctk.StringVar(value=self._settings.get(key, ''))
            entry = ctk.CTkEntry(parent, textvariable=var, show='*',
                                  placeholder_text=placeholder)
            entry.grid(row=row, column=1, padx=8, pady=4, sticky='ew')
            return var

        self._claude_key = _add_key_row('Claude API Key:', 'claude_api_key',
                                         'sk-ant-...', 1)
        self._claude_model_var = ctk.StringVar(
            value=self._settings.get('claude_model', 'claude-haiku-4-5-20251001'))
        ctk.CTkLabel(parent, text='Claude Model:', anchor='w').grid(
            row=2, column=0, padx=8, pady=4, sticky='w')
        ctk.CTkOptionMenu(
            parent,
            values=['claude-haiku-4-5-20251001', 'claude-sonnet-4-6', 'claude-opus-4-6'],
            variable=self._claude_model_var,
        ).grid(row=2, column=1, padx=8, pady=4, sticky='w')

        self._test_claude_lbl = ctk.CTkLabel(parent, text='', anchor='w',
                                               text_color='gray')
        self._test_claude_lbl.grid(row=3, column=1, padx=8, sticky='w')
        ctk.CTkButton(
            parent, text='Test Claude Connection', width=180,
            command=self._test_claude,
        ).grid(row=3, column=0, padx=8, pady=4)

        sep = ctk.CTkFrame(parent, height=1, fg_color='gray60')
        sep.grid(row=4, column=0, columnspan=2, sticky='ew', padx=8, pady=8)

        self._openai_key = _add_key_row('OpenAI API Key:', 'openai_api_key',
                                          'sk-...', 5)
        self._openai_model_var = ctk.StringVar(
            value=self._settings.get('openai_model', 'gpt-4o-mini'))
        ctk.CTkLabel(parent, text='OpenAI Model:', anchor='w').grid(
            row=6, column=0, padx=8, pady=4, sticky='w')
        ctk.CTkOptionMenu(
            parent,
            values=['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'],
            variable=self._openai_model_var,
        ).grid(row=6, column=1, padx=8, pady=4, sticky='w')

        self._test_openai_lbl = ctk.CTkLabel(parent, text='', anchor='w',
                                               text_color='gray')
        self._test_openai_lbl.grid(row=7, column=1, padx=8, sticky='w')
        ctk.CTkButton(
            parent, text='Test OpenAI Connection', width=180,
            command=self._test_openai,
        ).grid(row=7, column=0, padx=8, pady=4)

    def _test_claude(self) -> None:
        self._test_claude_lbl.configure(text='Testing...', text_color='gray')
        try:
            from app.ai.claude_provider import ClaudeProvider
            p = ClaudeProvider(self._claude_key.get(), self._claude_model_var.get())
            ok, msg = p.test_connection()
            self._test_claude_lbl.configure(
                text=f'✓ {msg}' if ok else f'✗ {msg}',
                text_color='#16a34a' if ok else '#dc2626',
            )
        except Exception as e:
            self._test_claude_lbl.configure(text=f'✗ {e}', text_color='#dc2626')

    def _test_openai(self) -> None:
        self._test_openai_lbl.configure(text='Testing...', text_color='gray')
        try:
            from app.ai.openai_provider import OpenAIProvider
            p = OpenAIProvider(self._openai_key.get(), self._openai_model_var.get())
            ok, msg = p.test_connection()
            self._test_openai_lbl.configure(
                text=f'✓ {msg}' if ok else f'✗ {msg}',
                text_color='#16a34a' if ok else '#dc2626',
            )
        except Exception as e:
            self._test_openai_lbl.configure(text=f'✗ {e}', text_color='#dc2626')

    # ── Sources tab ──────────────────────────────────────────────────────

    def _build_sources_tab(self, parent: ctk.CTkFrame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(parent)
        scroll.grid(row=0, column=0, sticky='nsew', pady=(0, 8))
        scroll.columnconfigure(1, weight=1)

        sources = self._repo.get_sources()
        for i, src in enumerate(sources):
            en_var = ctk.BooleanVar(value=bool(src['enabled']))
            ctk.CTkCheckBox(
                scroll, text='', variable=en_var, width=20,
                command=lambda s=src, v=en_var: self._repo.toggle_source(s['id'], v.get()),
            ).grid(row=i, column=0, padx=4, pady=2)

            cat_label = CATEGORY_LABELS.get(src['category'], src['category'])
            ctk.CTkLabel(
                scroll, text=f"[{cat_label}] {src['name']}", anchor='w',
            ).grid(row=i, column=1, sticky='ew', padx=4)

            ctk.CTkLabel(
                scroll, text=src['url'][:45] + '...', text_color='gray',
                font=ctk.CTkFont(size=10), anchor='w',
            ).grid(row=i, column=2, sticky='ew', padx=4)

            if src.get('custom'):
                ctk.CTkButton(
                    scroll, text='Del', width=40, height=22,
                    fg_color='#dc2626', hover_color='#b91c1c',
                    command=lambda s=src: self._delete_source(s, scroll, sources),
                ).grid(row=i, column=3, padx=4)

        # Add source form
        add_frame = ctk.CTkFrame(parent, fg_color='transparent')
        add_frame.grid(row=1, column=0, sticky='ew')
        add_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(add_frame, text='Add Source:', width=80, anchor='w').grid(
            row=0, column=0, padx=4, pady=4)

        self._new_name = ctk.CTkEntry(add_frame, placeholder_text='Name', width=100)
        self._new_name.grid(row=0, column=1, padx=4, pady=4, sticky='ew')

        self._new_url = ctk.CTkEntry(add_frame, placeholder_text='RSS URL')
        self._new_url.grid(row=0, column=2, padx=4, pady=4, sticky='ew')

        self._new_cat = ctk.CTkOptionMenu(
            add_frame,
            values=list(CATEGORY_LABELS.keys()),
            width=100,
        )
        self._new_cat.set('custom')
        self._new_cat.grid(row=0, column=3, padx=4, pady=4)

        ctk.CTkButton(add_frame, text='Add', width=60,
                       command=self._add_source).grid(row=0, column=4, padx=4)

    def _add_source(self) -> None:
        name = self._new_name.get().strip()
        url = self._new_url.get().strip()
        cat = self._new_cat.get()
        if name and url.startswith('http'):
            self._repo.add_source(name, url, cat, 'en', custom=True)
            self._new_name.delete(0, 'end')
            self._new_url.delete(0, 'end')

    def _delete_source(self, src: dict, scroll, sources: list) -> None:
        self._repo.delete_source(src['id'])
        # Rebuild the sources list (simplest approach: close and reopen dialog)

    # ── Preferences tab ──────────────────────────────────────────────────

    def _build_prefs_tab(self, parent: ctk.CTkFrame) -> None:
        parent.columnconfigure(1, weight=1)

        rows = [
            ('Theme:', 'theme', 'optionmenu', ['dark', 'light', 'system']),
            ('Articles per Page:', 'articles_per_page', 'optionmenu', ['15', '25', '50', '100']),
            ('Auto-Refresh:', 'auto_refresh_interval', 'optionmenu',
             ['0', '15', '30', '60'], 'minutes (0=off)'),
            ('Max Articles/Source:', 'max_articles_per_source', 'entry', None),
            ('Extract Full Text:', 'extract_full_text', 'checkbox', None),
            ('Auto AI Analysis:', 'auto_analyze', 'checkbox', None),
        ]

        self._pref_vars: dict[str, ctk.Variable] = {}
        for i, row_def in enumerate(rows):
            key = row_def[1]
            label = row_def[0]
            widget_type = row_def[2]
            current = self._settings.get(key, '')

            ctk.CTkLabel(parent, text=label, anchor='w').grid(
                row=i, column=0, padx=8, pady=6, sticky='w')

            if widget_type == 'optionmenu':
                values = row_def[3]
                var = ctk.StringVar(value=current)
                ctk.CTkOptionMenu(parent, values=values, variable=var, width=120).grid(
                    row=i, column=1, padx=8, pady=6, sticky='w')
                if len(row_def) > 4:
                    ctk.CTkLabel(parent, text=row_def[4], text_color='gray').grid(
                        row=i, column=2, padx=4, sticky='w')
            elif widget_type == 'entry':
                var = ctk.StringVar(value=current)
                ctk.CTkEntry(parent, textvariable=var, width=80).grid(
                    row=i, column=1, padx=8, pady=6, sticky='w')
            elif widget_type == 'checkbox':
                var = ctk.BooleanVar(value=current == '1')
                ctk.CTkCheckBox(parent, text='', variable=var).grid(
                    row=i, column=1, padx=8, pady=6, sticky='w')

            self._pref_vars[key] = var

    # ── Save ─────────────────────────────────────────────────────────────

    def _save(self) -> None:
        new_settings = {
            'ai_provider':            self._provider_var.get().lower(),
            'claude_api_key':         self._claude_key.get(),
            'openai_api_key':         self._openai_key.get(),
            'claude_model':           self._claude_model_var.get(),
            'openai_model':           self._openai_model_var.get(),
        }
        for key, var in self._pref_vars.items():
            val = var.get()
            if isinstance(val, bool):
                val = '1' if val else '0'
            new_settings[key] = str(val)

        self._repo.bulk_save_settings(new_settings)
        if self._on_save:
            self._on_save(new_settings)
        self.grab_release()
        self.destroy()
