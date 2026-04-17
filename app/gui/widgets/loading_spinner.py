import customtkinter as ctk

SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']


class LoadingSpinner(ctk.CTkFrame):
    """Non-blocking animated spinner with a status message."""

    def __init__(self, master, message: str = 'Loading...', **kwargs):
        super().__init__(master, fg_color=('gray90', 'gray15'), **kwargs)
        self._idx = 0
        self._running = False

        self._spinner_lbl = ctk.CTkLabel(self, text='', font=('Courier', 18))
        self._spinner_lbl.pack(pady=(20, 4))

        self._msg_lbl = ctk.CTkLabel(self, text=message)
        self._msg_lbl.pack(pady=(4, 20), padx=20)

    def start(self, message: str = '') -> None:
        if message:
            self._msg_lbl.configure(text=message)
        self._running = True
        self._animate()

    def stop(self) -> None:
        self._running = False

    def set_message(self, message: str) -> None:
        self._msg_lbl.configure(text=message)

    def _animate(self) -> None:
        if not self._running:
            return
        self._spinner_lbl.configure(text=SPINNER_FRAMES[self._idx % len(SPINNER_FRAMES)])
        self._idx += 1
        self.after(100, self._animate)
