from typing import Callable
import customtkinter as ctk


class InsightPanel(ctk.CTkFrame):
    """Compact newsroom dashboard for queue health and quick actions."""

    def __init__(
        self,
        master,
        on_status_filter: Callable[[str], None],
        on_analyze_queue: Callable[[], None],
        on_extract_missing: Callable[[], None],
        on_generate_report: Callable[[], None],
        **kwargs,
    ):
        super().__init__(
            master,
            height=116,
            corner_radius=0,
            fg_color=("#edf1f5", "#101418"),
            **kwargs,
        )
        self.grid_propagate(False)
        self._on_status_filter = on_status_filter
        self._on_analyze_queue = on_analyze_queue
        self._on_extract_missing = on_extract_missing
        self._on_generate_report = on_generate_report
        self._metric_values: dict[str, ctk.CTkLabel] = {}

        for col in range(7):
            self.columnconfigure(col, weight=1 if col < 5 else 0)
        self.rowconfigure(0, weight=1)

        self._build_metric("Total", "total", "#2563eb", 0, "all")
        self._build_metric("Unread", "unread", "#0f766e", 1, "unread")
        self._build_metric("Saved", "favorites", "#d97706", 2, "favorites")
        self._build_metric("AI ready", "analyzed", "#7c3aed", 3, "analyzed")
        self._build_metric("Today", "today", "#dc2626", 4, "all")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=5, columnspan=2, padx=(10, 14), pady=10, sticky="nsew")
        right.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right,
            text="Briefing Queue",
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="ew")

        self._queue_lbl = ctk.CTkLabel(
            right,
            text="No articles loaded",
            anchor="w",
            text_color=("gray35", "gray70"),
            font=ctk.CTkFont(size=11),
        )
        self._queue_lbl.grid(row=1, column=0, sticky="ew", pady=(2, 5))

        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew")
        actions.columnconfigure((0, 1, 2), weight=1)

        self._analyze_btn = ctk.CTkButton(
            actions,
            text="Analyze Queue",
            height=28,
            command=self._on_analyze_queue,
            fg_color=("#7c3aed", "#6d28d9"),
            hover_color=("#6d28d9", "#5b21b6"),
        )
        self._analyze_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._extract_btn = ctk.CTkButton(
            actions,
            text="Extract Text",
            height=28,
            command=self._on_extract_missing,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray85"),
            hover_color=("gray82", "gray25"),
        )
        self._extract_btn.grid(row=0, column=1, padx=4, sticky="ew")

        self._report_btn = ctk.CTkButton(
            actions,
            text="Topic Report",
            height=28,
            command=self._on_generate_report,
            fg_color="transparent",
            border_width=1,
            text_color=("gray20", "gray85"),
            hover_color=("gray82", "gray25"),
        )
        self._report_btn.grid(row=0, column=2, padx=(4, 0), sticky="ew")

    def _build_metric(
        self,
        label: str,
        key: str,
        accent: str,
        column: int,
        filter_key: str,
    ) -> None:
        card = ctk.CTkFrame(
            self,
            height=86,
            fg_color=("#ffffff", "#181d22"),
            corner_radius=8,
            border_width=1,
            border_color=("#d2d8df", "#2b333c"),
        )
        card.grid(row=0, column=column, padx=(12 if column == 0 else 5, 5), pady=10, sticky="nsew")
        card.grid_propagate(False)
        card.columnconfigure(0, weight=1)
        card.bind("<Button-1>", lambda _event: self._on_status_filter(filter_key))

        stripe = ctk.CTkFrame(card, fg_color=accent, width=4, corner_radius=2)
        stripe.place(x=12, y=14, relheight=0.68)

        title = ctk.CTkLabel(
            card,
            text=label,
            anchor="w",
            text_color=("gray35", "gray68"),
            font=ctk.CTkFont(size=11),
        )
        title.place(x=30, y=18, relwidth=0.78)
        title.bind("<Button-1>", lambda _event: self._on_status_filter(filter_key))

        value = ctk.CTkLabel(
            card,
            text="0",
            anchor="w",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        value.place(x=30, y=40, relwidth=0.78)
        value.bind("<Button-1>", lambda _event: self._on_status_filter(filter_key))
        self._metric_values[key] = value

    def update_stats(self, stats: dict, active_filter: str) -> None:
        for key in ("total", "unread", "favorites", "analyzed", "today"):
            self._metric_values[key].configure(text=str(stats.get(key, 0)))

        total = int(stats.get("total") or 0)
        analyzed = int(stats.get("analyzed") or 0)
        needs_ai = int(stats.get("needs_ai") or 0)
        needs_text = int(stats.get("needs_text") or 0)
        coverage = round((analyzed / total) * 100) if total else 0

        top_sources = stats.get("top_sources") or []
        if top_sources:
            source_text = ", ".join(f"{s['name']} {s['count']}" for s in top_sources)
        else:
            source_text = "No source activity yet"
        self._queue_lbl.configure(
            text=f"AI coverage {coverage}% | Needs AI {needs_ai} | Missing text {needs_text} | {source_text}"
        )

        self._analyze_btn.configure(
            text=f"Analyze Queue ({min(needs_ai, 5)})" if needs_ai else "Analyze Queue",
            state="normal" if needs_ai else "disabled",
        )
        self._extract_btn.configure(
            text=f"Extract Text ({min(needs_text, 50)})" if needs_text else "Extract Text",
            state="normal" if needs_text else "disabled",
        )
