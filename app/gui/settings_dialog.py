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
            value=self._settings.get('ai_provider', 'claude')
        )
        ctk.CTkLabel(parent, text='Active Provider:', anchor='w').grid(
            row=0, column=0, padx=8, pady=8, sticky='w')
        provider_menu = ctk.CTkSegmentedButton(
            parent,
            values=['claude', 'openai', 'siliconflow', 'deepseek', 'moonshot', 'zhipu', 'custom'],
            variable=self._provider_var,
            command=self._on_provider_changed,
            font=ctk.CTkFont(size=11),
        )
        provider_menu.grid(row=0, column=1, padx=8, pady=8, sticky='w')

        # Scrollable area for provider-specific fields
        self._ai_scroll = ctk.CTkScrollableFrame(parent, fg_color='transparent')
        self._ai_scroll.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=4)
        self._ai_scroll.columnconfigure(1, weight=1)
        parent.rowconfigure(1, weight=1)

        self._ai_field_widgets: list = []
        self._on_provider_changed(self._provider_var.get())

    def _on_provider_changed(self, provider: str) -> None:
        for w in self._ai_field_widgets:
            w.destroy()
        self._ai_field_widgets.clear()

        from app.ai.compat_provider import COMPAT_PRESETS

        def row(label, key, placeholder='', show='', row_idx=0):
            lbl = ctk.CTkLabel(self._ai_scroll, text=label, anchor='w')
            lbl.grid(row=row_idx, column=0, padx=8, pady=4, sticky='w')
            var = ctk.StringVar(value=self._settings.get(key, ''))
            ent = ctk.CTkEntry(self._ai_scroll, textvariable=var,
                               placeholder_text=placeholder,
                               show=show if show else '')
            ent.grid(row=row_idx, column=1, padx=8, pady=4, sticky='ew')
            self._ai_field_widgets += [lbl, ent]
            return var

        def model_row(label, key, placeholder, values, row_idx):
            lbl = ctk.CTkLabel(self._ai_scroll, text=label, anchor='w')
            lbl.grid(row=row_idx, column=0, padx=8, pady=4, sticky='w')
            var = ctk.StringVar(value=self._settings.get(key, ''))
            if values:
                w = ctk.CTkOptionMenu(self._ai_scroll, values=values, variable=var)
            else:
                w = ctk.CTkEntry(self._ai_scroll, textvariable=var,
                                 placeholder_text=placeholder)
            w.grid(row=row_idx, column=1, padx=8, pady=4, sticky='w')
            self._ai_field_widgets += [lbl, w]
            return var

        def test_row(label, test_fn, row_idx):
            lbl = ctk.CTkLabel(self._ai_scroll, text='', anchor='w', text_color='gray')
            lbl.grid(row=row_idx, column=1, padx=8, sticky='w')
            btn = ctk.CTkButton(self._ai_scroll, text=label, width=180,
                                command=lambda: test_fn(lbl))
            btn.grid(row=row_idx, column=0, padx=8, pady=4)
            self._ai_field_widgets += [lbl, btn]

        if provider == 'claude':
            self._claude_key = row('API Key:', 'claude_api_key', 'sk-ant-...', '*', 0)
            self._claude_model_var = model_row(
                'Model:', 'claude_model', '',
                ['claude-haiku-4-5-20251001', 'claude-sonnet-4-6', 'claude-opus-4-6'], 1)
            test_row('Test Connection', self._test_claude, 2)

        elif provider == 'openai':
            self._openai_key = row('API Key:', 'openai_api_key', 'sk-...', '*', 0)
            self._openai_model_var = model_row(
                'Model:', 'openai_model', '',
                ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'], 1)
            test_row('Test Connection', self._test_openai, 2)

        elif provider in COMPAT_PRESETS:
            _, default_model, display = COMPAT_PRESETS[provider]
            self._compat_key = row('API Key:', f'{provider}_api_key', '', '*', 0)
            self._compat_model_var = model_row(
                'Model:', f'{provider}_model', f'default: {default_model}', [], 1)
            test_row(f'Test {display}',
                     lambda lbl, p=provider: self._test_compat(lbl, p), 2)

        elif provider == 'custom':
            self._custom_key = row('API Key:', 'custom_api_key', '', '*', 0)
            self._custom_url = row('Base URL:', 'custom_base_url',
                                   'https://api.example.com/v1', '', 1)
            self._custom_model_var = model_row('Model:', 'custom_model', 'model-name', [], 2)
            self._custom_name_var = row('Provider Name:', 'custom_name', 'My Provider', '', 3)
            test_row('Test Connection',
                     lambda lbl: self._test_compat(lbl, 'custom'), 4)

    def _test_claude(self, lbl: ctk.CTkLabel) -> None:
        lbl.configure(text='Testing...', text_color='gray')
        try:
            from app.ai.claude_provider import ClaudeProvider
            p = ClaudeProvider(self._claude_key.get(), self._claude_model_var.get())
            ok, msg = p.test_connection()
            lbl.configure(text=f'✓ {msg}' if ok else f'✗ {msg}',
                          text_color='#16a34a' if ok else '#dc2626')
        except Exception as e:
            lbl.configure(text=f'✗ {e}', text_color='#dc2626')

    def _test_openai(self, lbl: ctk.CTkLabel) -> None:
        lbl.configure(text='Testing...', text_color='gray')
        try:
            from app.ai.openai_provider import OpenAIProvider
            p = OpenAIProvider(self._openai_key.get(), self._openai_model_var.get())
            ok, msg = p.test_connection()
            lbl.configure(text=f'✓ {msg}' if ok else f'✗ {msg}',
                          text_color='#16a34a' if ok else '#dc2626')
        except Exception as e:
            lbl.configure(text=f'✗ {e}', text_color='#dc2626')

    def _test_compat(self, lbl: ctk.CTkLabel, provider: str) -> None:
        lbl.configure(text='Testing...', text_color='gray')
        try:
            from app.ai.compat_provider import CompatProvider, COMPAT_PRESETS
            if provider in COMPAT_PRESETS:
                p = CompatProvider.from_preset(
                    provider,
                    api_key=self._compat_key.get(),
                    model_override=self._compat_model_var.get(),
                )
            else:
                p = CompatProvider(
                    api_key=self._custom_key.get(),
                    base_url=self._custom_url.get(),
                    model=self._custom_model_var.get(),
                    display_name=self._custom_name_var.get(),
                )
            ok, msg = p.test_connection()
            lbl.configure(text=f'✓ {msg}' if ok else f'✗ {msg}',
                          text_color='#16a34a' if ok else '#dc2626')
        except Exception as e:
            lbl.configure(text=f'✗ {e}', text_color='#dc2626')

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
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        form = ctk.CTkScrollableFrame(parent, fg_color='transparent')
        form.grid(row=0, column=0, sticky='nsew')
        form.columnconfigure(1, weight=1)

        rows = [
            ('Theme:', 'theme', 'optionmenu', ['dark', 'light', 'system']),
            ('Articles per Page:', 'articles_per_page', 'optionmenu', ['15', '25', '50', '100']),
            ('Auto-Refresh:', 'auto_refresh_interval', 'optionmenu',
             ['0', '15', '30', '60'], 'minutes (0=off)'),
            ('Max Articles/Source:', 'max_articles_per_source', 'entry', None),
            ('Extract Full Text:', 'extract_full_text', 'checkbox', None),
            ('Auto AI Analysis:', 'auto_analyze', 'checkbox', None),
            ('AI Report Language:', 'ai_report_language', 'optionmenu',
             ['English', '简体中文', '日本語', '한국어', 'Original language']),
            ('Topic Keywords:', 'topic_report_keywords', 'entry_wide', None,
             'Comma/semicolon separated, e.g. AI chips; Middle East'),
            ('Report Articles:', 'topic_report_max_articles', 'optionmenu',
             ['5', '10', '15', '20']),
            ('Auto Topic Reports:', 'auto_topic_reports', 'checkbox', None),
            ('Cleanup Enabled:', 'cleanup_enabled', 'checkbox', None),
            ('Cleanup on Refresh:', 'cleanup_on_refresh', 'checkbox', None),
            ('Max Article Age:', 'max_article_age_days', 'optionmenu',
             ['30', '60', '90', '180', '365'], 'days; favorites are kept'),
            ('Max Total Articles:', 'max_total_articles', 'optionmenu',
             ['500', '1000', '2000', '5000', '10000']),
        ]

        self._pref_vars: dict[str, ctk.Variable] = {}
        for i, row_def in enumerate(rows):
            key = row_def[1]
            label = row_def[0]
            widget_type = row_def[2]
            current = self._settings.get(key, '')

            ctk.CTkLabel(form, text=label, anchor='w').grid(
                row=i, column=0, padx=8, pady=6, sticky='w')

            if widget_type == 'optionmenu':
                values = row_def[3]
                var = ctk.StringVar(value=current)
                ctk.CTkOptionMenu(form, values=values, variable=var, width=120).grid(
                    row=i, column=1, padx=8, pady=6, sticky='w')
                if len(row_def) > 4:
                    ctk.CTkLabel(form, text=row_def[4], text_color='gray').grid(
                        row=i, column=2, padx=4, sticky='w')
            elif widget_type == 'entry':
                var = ctk.StringVar(value=current)
                ctk.CTkEntry(form, textvariable=var, width=80).grid(
                    row=i, column=1, padx=8, pady=6, sticky='w')
            elif widget_type == 'entry_wide':
                var = ctk.StringVar(value=current)
                ctk.CTkEntry(form, textvariable=var, width=330).grid(
                    row=i, column=1, padx=8, pady=6, sticky='ew')
                if len(row_def) > 4:
                    ctk.CTkLabel(form, text=row_def[4], text_color='gray',
                                 font=ctk.CTkFont(size=10)).grid(
                        row=i, column=2, padx=4, sticky='w')
            elif widget_type == 'checkbox':
                var = ctk.BooleanVar(value=current == '1')
                ctk.CTkCheckBox(form, text='', variable=var).grid(
                    row=i, column=1, padx=8, pady=6, sticky='w')

            self._pref_vars[key] = var

    # ── Save ─────────────────────────────────────────────────────────────

    def _save(self) -> None:
        provider = self._provider_var.get()
        from app.ai.compat_provider import COMPAT_PRESETS

        new_settings: dict[str, str] = {'ai_provider': provider}

        # Collect whichever key/model fields exist (vary by active provider tab)
        field_map = {
            'claude':      [('claude_api_key', '_claude_key'),
                            ('claude_model',   '_claude_model_var')],
            'openai':      [('openai_api_key', '_openai_key'),
                            ('openai_model',   '_openai_model_var')],
            'custom':      [('custom_api_key',  '_custom_key'),
                            ('custom_base_url', '_custom_url'),
                            ('custom_model',    '_custom_model_var'),
                            ('custom_name',     '_custom_name_var')],
        }
        for p in COMPAT_PRESETS:
            field_map[p] = [(f'{p}_api_key', '_compat_key'),
                            (f'{p}_model',   '_compat_model_var')]

        for setting_key, attr in field_map.get(provider, []):
            var = getattr(self, attr, None)
            if var is not None:
                new_settings[setting_key] = var.get()

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
