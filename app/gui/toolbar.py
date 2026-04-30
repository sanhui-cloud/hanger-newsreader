from typing import Callable
import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    """Top toolbar: refresh, search, status filters, AI, settings."""

    def __init__(
        self,
        master,
        on_refresh: Callable,
        on_search: Callable[[str], None],
        on_status_filter: Callable[[str], None],
        on_ai_analyze: Callable,
        on_settings: Callable,
        **kwargs,
    ):
        super().__init__(
            master,
            height=60,
            corner_radius=0,
            fg_color=("#f6f8fb", "#0f1318"),
            **kwargs,
        )
        self.grid_propagate(False)
        self.pack_propagate(False)
        self._on_search = on_search
        self._on_status_filter = on_status_filter
        self._search_after_id = None
        self._filter_labels = {
            "All": "all",
            "Unread": "unread",
            "Saved": "favorites",
            "AI": "analyzed",
        }

        self._refresh_btn = ctk.CTkButton(
            self,
            text='Refresh',
            width=92,
            height=34,
            command=on_refresh,
        )
        self._refresh_btn.pack(side='left', padx=(12, 6), pady=12)

        self._search_entry = ctk.CTkEntry(
            self,
            placeholder_text='Search title, source, summary, full text...',
            width=360,
            height=34,
        )
        self._search_entry.pack(side='left', padx=4, pady=12)
        self._search_entry.bind('<KeyRelease>', self._on_key)

        self._clear_btn = ctk.CTkButton(
            self,
            text='X',
            width=30,
            height=30,
            fg_color='transparent', hover_color=('gray80', 'gray30'),
            command=self._clear_search,
        )
        self._clear_btn.pack(side='left', padx=(0, 10), pady=12)

        self._status_filter = ctk.CTkSegmentedButton(
            self,
            values=list(self._filter_labels.keys()),
            command=self._emit_status_filter,
            height=32,
            font=ctk.CTkFont(size=12),
        )
        self._status_filter.set("All")
        self._status_filter.pack(side='left', padx=6, pady=12)

        # Spacer
        ctk.CTkFrame(self, fg_color='transparent').pack(side='left', fill='x', expand=True)

        self._ai_btn = ctk.CTkButton(
            self,
            text='Analyze Article',
            width=124,
            height=34,
            command=on_ai_analyze,
            fg_color=('#7c3aed', '#6d28d9'),
            hover_color=('#6d28d9', '#5b21b6'),
            state='disabled',
        )
        self._ai_btn.pack(side='left', padx=6, pady=12)

        ctk.CTkButton(
            self,
            text='Settings',
            width=94,
            height=34,
            command=on_settings,
            fg_color='transparent',
            hover_color=('gray80', 'gray30'),
            text_color=('gray20', 'gray80'),
        ).pack(side='left', padx=(4, 12), pady=12)

    def set_busy(self, busy: bool) -> None:
        self._refresh_btn.configure(
            state='disabled' if busy else 'normal',
            text='Working...' if busy else 'Refresh',
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

    def _emit_status_filter(self, label: str) -> None:
        self._on_status_filter(self._filter_labels.get(label, "all"))

    def set_status_filter(self, status_filter: str) -> None:
        for label, value in self._filter_labels.items():
            if value == status_filter:
                self._status_filter.set(label)
                return
