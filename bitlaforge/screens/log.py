"""BitlaForge — Log screen.

The streaming log view for minerd's stdout. v0.1.0 is a stub:
  • the search Input + auto-scroll Checkbox compose,
  • the log buffer is empty (no minerd subprocess yet),
  • `appendLogLine(line)` and the 5,000-line bounded ring are wired so
    Phase B can pipe minerd output straight into this screen with no
    further wiring.

5,000-line cap and the search/auto-scroll surface are carried forward
from the Qt scaffold's design.
"""

from collections import deque

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Label, Static, Input, Checkbox
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer

from ..widgets.status import StatusMixin


_MAX_LOG_LINES = 5000


class LogScreen(StatusMixin, Container):
    """Streaming view of minerd stdout."""

    STATUS_WIDGET_ID = "log-status"
    DEFAULT_FOCUS = "#log-search"

    BINDINGS = [
        Binding("slash", "focus_search", "Search", show=True),
        Binding("c",     "clear_log",    "Clear",  show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Bounded ring so the buffer can't grow without limit during long
        # mining sessions (the Qt scaffold's 5,000-line cap, carried over).
        self._buffer: deque[str] = deque(maxlen=_MAX_LOG_LINES)
        self._filter: str = ""

    def compose(self) -> ComposeResult:
        with Vertical(classes="main-area"):
            yield Label("📜  Log  (live minerd output)", classes="section-title")
            with Horizontal(classes="log-controls"):
                yield Input(placeholder="Filter…", id="log-search")
                yield Checkbox("Auto-scroll", value=True, id="log-autoscroll")
            with ScrollableContainer(id="log-view-container"):
                yield Static("", id="log-view")
            yield Label("", id="log-status")

    def on_mount(self) -> None:
        self._redraw()
        self._set_status(
            f"Log buffer ready ({_MAX_LOG_LINES}-line cap).", "info", popup=False,
        )

    def on_show(self) -> None:
        self._redraw()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "log-search":
            self._filter = event.value.strip()
            self._redraw()

    def append_line(self, line: str) -> None:
        """Add one line to the buffer and re-render. Phase B plumbs this in."""
        self._buffer.append(line)
        self._redraw()

    def _redraw(self) -> None:
        """Render the (optionally filtered) buffer into the log view.

        NOTE: this method is called `_redraw`, not `_render`, because `_render`
        would shadow Textual's internal `Widget._render()` — silent breakage
        where the screen renders as `None` and the whole app errors.
        """
        if self._filter:
            lines = [ln for ln in self._buffer if self._filter.lower() in ln.lower()]
        else:
            lines = list(self._buffer)

        if not lines:
            text = "[#6c7086]  (no log lines yet — start the miner with M)[/]"
        else:
            text = "\n".join(lines)
        self.query_one("#log-view", Static).update(text)

    def action_focus_search(self) -> None:
        self.query_one("#log-search", Input).focus()

    def action_clear_log(self) -> None:
        self._buffer.clear()
        self._redraw()
        self._set_status("Log buffer cleared.", "info")

    def action_refresh(self) -> None:
        self._redraw()
        self._set_status("Log view refreshed.", "info")
