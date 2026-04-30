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
        self._category_counts: dict[str, tuple[int, int]] = {}
        self._on_add_source: Callable | None = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill='x', padx=8, pady=(10, 4))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text='Sources', font=ctk.CTkFont(size=14, weight='bold'),
            anchor='w',
        ).grid(row=0, column=0, sticky='ew')

        quick = ctk.CTkFrame(header, fg_color="transparent")
        quick.grid(row=0, column=1, sticky='e')
        ctk.CTkButton(
            quick,
            text='All',
            width=34,
            height=22,
            fg_color='transparent',
            border_width=1,
            text_color=('gray25', 'gray75'),
            hover_color=('gray84', 'gray26'),
            font=ctk.CTkFont(size=10),
            command=self.select_all,
        ).pack(side='left', padx=(0, 3))
        ctk.CTkButton(
            quick,
            text='None',
            width=44,
            height=22,
            fg_color='transparent',
            border_width=1,
            text_color=('gray25', 'gray75'),
            hover_color=('gray84', 'gray26'),
            font=ctk.CTkFont(size=10),
            command=self.select_none,
        ).pack(side='left')

    def set_sources(self, sources: list[dict],
                    on_add_source: Callable | None = None) -> None:
        """Rebuild sidebar from sources list."""
        self._on_add_source = on_add_source
        # Destroy old content (except header row)
        for child in list(self.winfo_children())[1:]:
            child.destroy()
        self._source_vars.clear()
        self._category_frames.clear()
        self._category_counts.clear()

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
        enabled_count = sum(1 for src in sources if src.get('enabled', 1))
        self._category_counts[category] = (enabled_count, len(sources))

        # Section header (toggle button)
        header = ctk.CTkButton(
            self,
            text=f'{"+" if collapsed else "-"} {label}  {enabled_count}/{len(sources)}',
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

            cb = ctk.CTkCheckBox(
                children,
                text=src['name'],
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
                # Re-insert the children frame immediately after its header
                frame.pack(fill='x', padx=4, after=header)
            label = CATEGORY_LABELS.get(category, category.title())
            enabled, total = self._category_counts.get(category, (0, 0))
            header.configure(text=f'{"+" if collapsed else "-"} {label}  {enabled}/{total}')

    def _emit_filter(self) -> None:
        enabled_ids = [sid for sid, var in self._source_vars.items() if var.get()]
        self._on_filter_change(enabled_ids)

    def get_enabled_source_ids(self) -> list[int]:
        return [sid for sid, var in self._source_vars.items() if var.get()]

    def select_all(self, category: str | None = None) -> None:
        for sid, var in self._source_vars.items():
            var.set(True)
        self._emit_filter()

    def select_none(self) -> None:
        for sid, var in self._source_vars.items():
            var.set(False)
        self._emit_filter()
