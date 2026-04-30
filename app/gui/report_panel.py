from typing import Callable, Optional
import customtkinter as ctk


class ReportPanel(ctk.CTkFrame):
    """Generated topic reports list and viewer."""

    def __init__(
        self,
        master,
        on_generate: Callable[[], None],
        on_export: Callable[[dict], None],
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self._on_generate = on_generate
        self._on_export = on_export
        self._reports: list[dict] = []
        self._current_report: Optional[dict] = None
        self._cards: list[ctk.CTkFrame] = []

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.grid(row=0, column=0, sticky='ew', padx=12, pady=(10, 6))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text='Topic Reports',
            anchor='w',
            font=ctk.CTkFont(size=16, weight='bold'),
        ).grid(row=0, column=0, sticky='ew')

        ctk.CTkButton(
            header,
            text='Generate from Keywords',
            width=168,
            height=30,
            fg_color=('#7c3aed', '#6d28d9'),
            hover_color=('#6d28d9', '#5b21b6'),
            command=self._on_generate,
        ).grid(row=0, column=1, padx=(8, 0))

        self._export_btn = ctk.CTkButton(
            header,
            text='Export MD',
            width=92,
            height=30,
            fg_color='transparent',
            border_width=1,
            text_color=('gray20', 'gray80'),
            hover_color=('gray82', 'gray26'),
            command=self._export_current,
            state='disabled',
        )
        self._export_btn.grid(row=0, column=2, padx=(8, 0))

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color='transparent')
        body.grid(row=1, column=0, sticky='nsew', padx=8, pady=(0, 8))
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=0, minsize=260)
        body.columnconfigure(1, weight=1)

        self._list = ctk.CTkScrollableFrame(body, width=260)
        self._list.grid(row=0, column=0, sticky='ns', padx=(0, 6))
        self._list.columnconfigure(0, weight=1)

        viewer = ctk.CTkFrame(body)
        viewer.grid(row=0, column=1, sticky='nsew')
        viewer.rowconfigure(1, weight=1)
        viewer.columnconfigure(0, weight=1)

        self._title_lbl = ctk.CTkLabel(
            viewer,
            text='Select a report',
            anchor='w',
            font=ctk.CTkFont(size=14, weight='bold'),
        )
        self._title_lbl.grid(row=0, column=0, padx=10, pady=(10, 4), sticky='ew')

        self._report_box = ctk.CTkTextbox(
            viewer,
            state='disabled',
            wrap='word',
            font=ctk.CTkFont(family='Microsoft YaHei', size=13),
        )
        self._report_box.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))
        self._set_text('No reports yet. Configure Topic Keywords in Settings, then generate a report.')

    def display_reports(self, reports: list[dict]) -> None:
        self._reports = reports
        self._cards.clear()
        for child in self._list.winfo_children():
            child.destroy()

        if not reports:
            ctk.CTkLabel(
                self._list,
                text='No reports yet.',
                text_color='gray',
                wraplength=220,
            ).grid(row=0, column=0, padx=10, pady=20)
            return

        for row, report in enumerate(reports):
            card = self._make_card(report)
            card.grid(row=row, column=0, sticky='ew', padx=4, pady=3)
            self._cards.append(card)

        if not self._current_report:
            self.select_report(reports[0])

    def _make_card(self, report: dict) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._list,
            corner_radius=8,
            border_width=1,
            border_color=('#d7dde5', '#2b333c'),
            fg_color=('#ffffff', '#171b20'),
            cursor='hand2',
        )
        card.columnconfigure(0, weight=1)
        title = ctk.CTkLabel(
            card,
            text=report.get('title', 'Untitled report'),
            anchor='w',
            justify='left',
            wraplength=210,
            font=ctk.CTkFont(size=12, weight='bold'),
        )
        title.grid(row=0, column=0, padx=8, pady=(8, 2), sticky='ew')

        keywords = ', '.join(report.get('keywords', []))
        meta = f"{report.get('created_at', '')[:16]} · {keywords}"
        ctk.CTkLabel(
            card,
            text=meta,
            anchor='w',
            justify='left',
            wraplength=210,
            text_color='gray',
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=0, padx=8, pady=(0, 8), sticky='ew')

        self._bind_card(card, report)
        return card

    def _bind_card(self, widget, report: dict) -> None:
        widget.bind('<Button-1>', lambda _event: self.select_report(report))
        for child in widget.winfo_children():
            self._bind_card(child, report)

    def select_report(self, report: dict) -> None:
        self._current_report = report
        self._title_lbl.configure(text=report.get('title', 'Untitled report'))
        self._set_text(report.get('report', ''))
        self._export_btn.configure(state='normal')

    def _set_text(self, text: str) -> None:
        self._report_box.configure(state='normal')
        self._report_box.delete('1.0', 'end')
        self._report_box.insert('1.0', text)
        self._report_box.configure(state='disabled')
        self._report_box.yview_moveto(0)

    def _export_current(self) -> None:
        if self._current_report:
            self._on_export(self._current_report)
