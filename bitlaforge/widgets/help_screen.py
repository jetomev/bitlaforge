"""BitlaForge — Help modal screen.

Ported from alacrittyForge v0.1.1's hardened HelpScreen. Toggles instead
of stacking (app's `action_show_help` is the gate); Esc / q / ? all
dismiss. q is bound here so it shadows the app-level quit while help is
up.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Label
from textual.containers import Vertical


class HelpScreen(ModalScreen):
    """Toggleable, dismissible help overlay."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    HelpScreen > Vertical {
        background: #181825;
        border: solid #cba6f7;
        padding: 2 4;
        width: 64;
        height: auto;
    }
    HelpScreen .help-title {
        color: #cba6f7;
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }
    HelpScreen .help-line {
        color: #cdd6f4;
    }
    HelpScreen .help-section {
        color: #f9e2af;
        text-style: bold;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape",        "close", "Close"),
        Binding("q",             "close", "Close"),
        Binding("question_mark", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("⚡ BitlaForge — Help", classes="help-title")
            yield Label("── Global ───────────────────────────", classes="help-section")
            yield Label("  1-3    Switch screens",       classes="help-line")
            yield Label("  M      Start / stop miner",   classes="help-line")
            yield Label("  R      Refresh current screen", classes="help-line")
            yield Label("  q      Quit",                 classes="help-line")
            yield Label("  ?      Toggle this help",     classes="help-line")
            yield Label("── Dashboard ────────────────────────", classes="help-section")
            yield Label("  (read-only overview of miner state)", classes="help-line")
            yield Label("── Log ──────────────────────────────", classes="help-section")
            yield Label("  /      Focus search filter",  classes="help-line")
            yield Label("  C      Clear log buffer",     classes="help-line")
            yield Label("── Config ───────────────────────────", classes="help-section")
            yield Label("  E      Edit selected field",  classes="help-line")
            yield Label("  S      Save configuration",   classes="help-line")
            yield Label("", classes="help-line")
            yield Label("  Press Esc, q, or ? to close", classes="help-section")

    def action_close(self) -> None:
        self.dismiss(None)
