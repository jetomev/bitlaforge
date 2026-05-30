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

from ..config_manager import load_config, save_config, DEFAULT_CONFIG, CONFIG_PATH
from ..widgets.status import StatusMixin
from ..widgets.confirm_dialog import ConfirmDialog


_DEFAULT_ALGORITHM = DEFAULT_CONFIG["algorithm"]
_AVAILABLE_ALGORITHMS = [
    "sha256d", "scrypt", "yescrypt", "x11", "x13", "x15", "x17", "groestl",
]


class ConfigScreen(StatusMixin, Container):
    """Edit the miner's pool/wallet/algorithm/thread settings."""

    STATUS_WIDGET_ID = "config-status"
    # Focus the screen container, NOT an Input — Inputs absorb digit keys
    # and wallets/pool ports contain digits, so we don't want them captured
    # for navigation. The user presses E to enter edit mode (focuses the
    # first input); clicking the sidebar or pressing 1/2/3 navigates out.
    can_focus = True
    DEFAULT_FOCUS = "#config"

    BINDINGS = [
        Binding("e", "focus_first",  "Edit", show=True),
        Binding("s", "save_config",  "Save", show=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # G1 (v0.1.1): config is loaded from ~/.config/bitlaforge/config.toml.
        # First launch returns DEFAULT_CONFIG; persists across launches.
        self._config: dict = load_config()

    def compose(self) -> ComposeResult:
        with Vertical(classes="main-area"):
            yield Label("⚙   Miner Configuration", classes="section-title")
            yield Static(
                "[#a6adc8]Settings used when starting `minerd`. "
                "Press S to save, E to begin editing.[/]",
                classes="detail-muted",
            )

            yield Label(
                "Name  (local label + pool worker name, e.g. \"laptop-rig\")",
                classes="field-label",
            )
            yield Input(placeholder="this-machine", id="config-miner-name")

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

            # G2: dynamic "of N available" hint — sourced from os.cpu_count()
            # so the user immediately sees their ceiling.
            from ..system_info import get_system_info
            _cores_avail = get_system_info().logical_cores
            yield Label(
                f"Thread count  (0 = auto-detect, of {_cores_avail} available)",
                classes="field-label",
            )
            yield Input(placeholder="0", id="config-threads")

            yield Label(
                "Niceness  (0 = normal priority, 19 = lowest — recommended for "
                "background mining)",
                classes="field-label",
            )
            yield Input(placeholder="19", id="config-niceness")

            with Horizontal(classes="config-buttons"):
                yield Button("Save",         id="btn-save",  classes="primary")
                yield Button("Revert",       id="btn-revert", classes="warning")

            yield Label("", id="config-status")

    def on_mount(self) -> None:
        self._populate_inputs()
        if CONFIG_PATH.exists():
            self._set_status(
                f"Config loaded from {CONFIG_PATH}", "info", popup=False,
            )
        else:
            self._set_status(
                "No saved config yet — fill in pool + wallet and press S to save.",
                "info", popup=False,
            )

    def on_show(self) -> None:
        # Silent reload — preserves any unsaved field edits the user typed
        # before switching screens (the alacrittyForge G1 lesson).
        pass

    def _populate_inputs(self) -> None:
        """Push current config values into the input widgets."""
        self.query_one("#config-miner-name", Input).value = self._config.get("miner_name", "")
        self.query_one("#config-pool",       Input).value = self._config["pool"]
        self.query_one("#config-wallet",     Input).value = self._config["wallet"]
        self.query_one("#config-threads",    Input).value = self._config["threads"]
        self.query_one("#config-niceness",   Input).value = self._config.get("niceness", "19")
        self.query_one("#config-algorithm",  Select).value = self._config["algorithm"]

    def _read_inputs(self) -> dict:
        return {
            "miner_name": self.query_one("#config-miner-name", Input).value.strip(),
            "pool":       self.query_one("#config-pool",       Input).value.strip(),
            "wallet":     self.query_one("#config-wallet",     Input).value.strip(),
            "threads":    self.query_one("#config-threads",    Input).value.strip() or "0",
            "niceness":   self.query_one("#config-niceness",   Input).value.strip() or "19",
            "algorithm":  str(self.query_one("#config-algorithm", Select).value or _DEFAULT_ALGORITHM),
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
            if save_config(new_config):
                self._config = new_config
                self._set_status(
                    f"Saved to {CONFIG_PATH}", "ok",
                )
            else:
                self._set_status(
                    f"Failed to write {CONFIG_PATH} — check permissions.",
                    "error",
                )

        self.app.push_screen(
            ConfirmDialog(
                title="Save Miner Configuration",
                message=(
                    f"Save these settings?\n"
                    f"  name: {new_config['miner_name']}\n"
                    f"  pool: {new_config['pool']}\n"
                    f"  wallet: {new_config['wallet']}\n"
                    f"  algorithm: {new_config['algorithm']}\n"
                    f"  threads: {new_config['threads']}\n"
                    f"  niceness: {new_config['niceness']}"
                ),
            ),
            on_confirm,
        )

    def action_refresh(self) -> None:
        self._populate_inputs()
        self._set_status("Config view refreshed.", "info")
