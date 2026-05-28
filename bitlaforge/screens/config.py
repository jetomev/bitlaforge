"""BitlaForge — Config screen.

Capture the minerd command-line knobs: pool URL, wallet address, algorithm,
thread count. v0.1.0 holds them in memory only — Phase B / v0.1.2 wires
persistence to `~/.config/bitlaforge/config.toml` and uses these values
when spawning the minerd subprocess.

Field surface carried forward from the Qt scaffold's "Configure Miner"
dialog (the modal becomes a full screen — more TUI-natural).
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Label, Static, Input, Button, Select
from textual.containers import Container, Vertical, Horizontal

from ..widgets.status import StatusMixin
from ..widgets.confirm_dialog import ConfirmDialog


_DEFAULT_ALGORITHM = "sha256d"
_AVAILABLE_ALGORITHMS = [
    "sha256d", "scrypt", "yescrypt", "x11", "x13", "x15", "x17", "groestl",
]


class ConfigScreen(StatusMixin, Container):
    """Edit the miner's pool/wallet/algorithm/thread settings."""

    STATUS_WIDGET_ID = "config-status"
    DEFAULT_FOCUS = "#config-pool"

    BINDINGS = [
        Binding("e", "focus_first",  "Edit", show=True),
        Binding("s", "save_config",  "Save", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # In-memory config for v0.1.0 (persisted in v0.1.2).
        self._config: dict = {
            "pool": "",
            "wallet": "",
            "algorithm": _DEFAULT_ALGORITHM,
            "threads": "0",  # 0 = auto-detect
        }

    def compose(self) -> ComposeResult:
        with Vertical(classes="main-area"):
            yield Label("⚙   Miner Configuration", classes="section-title")
            yield Static(
                "[#a6adc8]Settings used when starting `minerd`. "
                "Press S to save, E to begin editing.[/]",
                classes="detail-muted",
            )

            yield Label("Pool URL (host:port or stratum+tcp://…)", classes="field-label")
            yield Input(
                placeholder="stratum+tcp://pool.example.com:3333",
                id="config-pool",
            )

            yield Label("Wallet address (Bitcoin payout)", classes="field-label")
            yield Input(placeholder="bc1q…", id="config-wallet")

            yield Label("Algorithm", classes="field-label")
            yield Select(
                [(a, a) for a in _AVAILABLE_ALGORITHMS],
                id="config-algorithm",
                value=_DEFAULT_ALGORITHM,
            )

            yield Label("Thread count  (0 = auto-detect)", classes="field-label")
            yield Input(placeholder="0", id="config-threads")

            with Horizontal(classes="config-buttons"):
                yield Button("Save",         id="btn-save",  classes="primary")
                yield Button("Revert",       id="btn-revert", classes="warning")

            yield Label("", id="config-status")

    def on_mount(self) -> None:
        self._populate_inputs()
        self._set_status(
            "Config loaded (in-memory; persistence lands in v0.1.2).",
            "info", popup=False,
        )

    def on_show(self) -> None:
        # Silent reload — preserves any unsaved field edits the user typed
        # before switching screens (the alacrittyForge G1 lesson).
        pass

    def _populate_inputs(self) -> None:
        """Push current config values into the input widgets."""
        self.query_one("#config-pool",      Input).value = self._config["pool"]
        self.query_one("#config-wallet",    Input).value = self._config["wallet"]
        self.query_one("#config-threads",   Input).value = self._config["threads"]
        self.query_one("#config-algorithm", Select).value = self._config["algorithm"]

    def _read_inputs(self) -> dict:
        return {
            "pool":      self.query_one("#config-pool",    Input).value.strip(),
            "wallet":    self.query_one("#config-wallet",  Input).value.strip(),
            "threads":   self.query_one("#config-threads", Input).value.strip() or "0",
            "algorithm": str(self.query_one("#config-algorithm", Select).value or _DEFAULT_ALGORITHM),
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save_config()
        elif event.button.id == "btn-revert":
            self._populate_inputs()
            self._set_status("Reverted to last-saved config.", "info")

    def action_focus_first(self) -> None:
        self.query_one("#config-pool", Input).focus()

    def action_save_config(self) -> None:
        """Save the current input values to in-memory config (v0.1.0)."""
        new_config = self._read_inputs()

        # Basic validation — pool + wallet are required to actually start.
        missing = [k for k in ("pool", "wallet") if not new_config[k]]
        if missing:
            self._set_status(
                f"Missing required field(s): {', '.join(missing)}.",
                "warn",
            )
            return

        def on_confirm(confirmed: bool) -> None:
            if not confirmed:
                self._set_status("Save cancelled.", "info")
                return
            self._config = new_config
            self._set_status(
                "Configuration saved (in-memory until v0.1.2).", "ok",
            )

        self.app.push_screen(
            ConfirmDialog(
                title="Save Miner Configuration",
                message=(
                    f"Save these settings?\n"
                    f"  pool: {new_config['pool']}\n"
                    f"  wallet: {new_config['wallet']}\n"
                    f"  algorithm: {new_config['algorithm']}\n"
                    f"  threads: {new_config['threads']}"
                ),
            ),
            on_confirm,
        )

    def action_refresh(self) -> None:
        self._populate_inputs()
        self._set_status("Config view refreshed.", "info")
