from typing import Callable
import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    """Top toolbar: Refresh, search bar, AI Analyze, Settings."""

    def __init__(
        self,
        master,
        on_refresh: Callable,
        on_search: Callable[[str], None],
        on_ai_analyze: Callable,
        on_settings: Callable,
        **kwargs,
    ):
        super().__init__(master, height=52, corner_radius=0, **kwargs)
        self.grid_propagate(False)
        self._on_search = on_search
        self._search_after_id = None

        self._refresh_btn = ctk.CTkButton(
            self, text='⟳ Refresh', width=90, command=on_refresh,
        )
        self._refresh_btn.pack(side='left', padx=(10, 4), pady=8)

        self._search_entry = ctk.CTkEntry(
            self, placeholder_text='Search articles...', width=280,
        )
        self._search_entry.pack(side='left', padx=4, pady=8)
        self._search_entry.bind('<KeyRelease>', self._on_key)

        self._clear_btn = ctk.CTkButton(
            self, text='✕', width=28, height=28,
            fg_color='transparent', hover_color=('gray80', 'gray30'),
            command=self._clear_search,
        )
        self._clear_btn.pack(side='left', padx=(0, 8), pady=8)

        # Spacer
        ctk.CTkFrame(self, fg_color='transparent').pack(side='left', fill='x', expand=True)

        self._ai_btn = ctk.CTkButton(
            self, text='✦ AI Analyze', width=110, command=on_ai_analyze,
            fg_color=('#7c3aed', '#6d28d9'),
            hover_color=('#6d28d9', '#5b21b6'),
            state='disabled',
        )
        self._ai_btn.pack(side='left', padx=4, pady=8)

        ctk.CTkButton(
            self, text='⚙ Settings', width=90, command=on_settings,
            fg_color='transparent',
            hover_color=('gray80', 'gray30'),
            text_color=('gray20', 'gray80'),
        ).pack(side='left', padx=(4, 10), pady=8)

    def set_busy(self, busy: bool) -> None:
        self._refresh_btn.configure(
            state='disabled' if busy else 'normal',
            text='...' if busy else '⟳ Refresh',
        )

    def enable_ai_button(self, enabled: bool) -> None:
        self._ai_btn.configure(state='normal' if enabled else 'disabled')

    def get_search_text(self) -> str:
        return self._search_entry.get().strip()

    def _on_key(self, _event=None) -> None:
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(400, lambda: self._on_search(self.get_search_text()))

    def _clear_search(self) -> None:
        self._search_entry.delete(0, 'end')
        self._on_search('')
