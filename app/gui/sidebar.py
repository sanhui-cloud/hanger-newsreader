from typing import Callable
import customtkinter as ctk
from app.config import CATEGORY_LABELS, CATEGORY_COLORS


class Sidebar(ctk.CTkScrollableFrame):
    """Left panel: collapsible source filter tree."""

    def __init__(self, master, on_filter_change: Callable[[list[int]], None], **kwargs):
        super().__init__(master, width=210, **kwargs)
        self._on_filter_change = on_filter_change
        self._source_vars: dict[int, ctk.BooleanVar] = {}
        self._category_frames: dict[str, ctk.CTkFrame] = {}
        self._category_collapsed: dict[str, bool] = {}
        self._on_add_source: Callable | None = None

        ctk.CTkLabel(
            self, text='News Sources', font=ctk.CTkFont(size=13, weight='bold'),
            anchor='w',
        ).pack(fill='x', padx=8, pady=(8, 4))

    def set_sources(self, sources: list[dict],
                    on_add_source: Callable | None = None) -> None:
        """Rebuild sidebar from sources list."""
        self._on_add_source = on_add_source
        # Destroy old content (except header label)
        for child in list(self.winfo_children())[1:]:
            child.destroy()
        self._source_vars.clear()
        self._category_frames.clear()

        # Group by category
        categories: dict[str, list[dict]] = {}
        for src in sources:
            cat = src.get('category', 'custom')
            categories.setdefault(cat, []).append(src)

        for cat in ['western', 'chinese', 'japanese', 'middleeast', 'custom']:
            srcs = categories.get(cat, [])
            if not srcs:
                continue
            self._build_category_section(cat, srcs)

        # Add source button
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(fill='x', padx=4, pady=(8, 4))
        ctk.CTkButton(
            btn_frame, text='+ Add Source', height=28,
            fg_color='transparent', border_width=1,
            text_color=('gray30', 'gray70'),
            hover_color=('gray85', 'gray25'),
            command=lambda: on_add_source() if on_add_source else None,
        ).pack(fill='x')

    def _build_category_section(self, category: str, sources: list[dict]) -> None:
        label = CATEGORY_LABELS.get(category, category.title())
        colors = CATEGORY_COLORS.get(category, ('#6b7280', '#4b5563'))
        collapsed = self._category_collapsed.get(category, False)

        # Section header (toggle button)
        header = ctk.CTkButton(
            self,
            text=f'{"▶" if collapsed else "▼"} {label}',
            anchor='w',
            height=28,
            fg_color=colors,
            hover_color=(colors[1], colors[1]),
            font=ctk.CTkFont(size=11, weight='bold'),
            command=lambda c=category: self._toggle_category(c),
        )
        header.pack(fill='x', padx=4, pady=(4, 0))
        self._category_frames[category + '_header'] = header

        # Children frame
        children = ctk.CTkFrame(self, fg_color='transparent')
        if not collapsed:
            children.pack(fill='x', padx=4)
        self._category_frames[category] = children

        for src in sources:
            var = ctk.BooleanVar(value=bool(src.get('enabled', 1)))
            self._source_vars[src['id']] = var

            flag = self._flag_for_category(category)
            cb = ctk.CTkCheckBox(
                children,
                text=f"{flag} {src['name']}",
                variable=var,
                font=ctk.CTkFont(size=11),
                command=self._emit_filter,
                checkbox_width=16,
                checkbox_height=16,
            )
            cb.pack(anchor='w', padx=(16, 4), pady=1)

    def _toggle_category(self, category: str) -> None:
        collapsed = not self._category_collapsed.get(category, False)
        self._category_collapsed[category] = collapsed
        frame = self._category_frames.get(category)
        header = self._category_frames.get(category + '_header')
        if frame and header:
            if collapsed:
                frame.pack_forget()
            else:
                frame.pack(fill='x', padx=4)
            # Update arrow
            label = CATEGORY_LABELS.get(category, category.title())
            header.configure(text=f'{"▶" if collapsed else "▼"} {label}')

    def _emit_filter(self) -> None:
        enabled_ids = [sid for sid, var in self._source_vars.items() if var.get()]
        self._on_filter_change(enabled_ids)

    def get_enabled_source_ids(self) -> list[int]:
        return [sid for sid, var in self._source_vars.items() if var.get()]

    def select_all(self, category: str | None = None) -> None:
        for sid, var in self._source_vars.items():
            var.set(True)
        self._emit_filter()

    @staticmethod
    def _flag_for_category(category: str) -> str:
        return {'western': '🌎', 'chinese': '🇨🇳', 'japanese': '🇯🇵',
                'middleeast': '🌙', 'custom': '⭐'}.get(category, '•')
