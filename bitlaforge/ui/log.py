"""Log — what the miner says, in plain words where it matters (v1.0.0).

Show: Important (no per-core speed lines), Everything, Problems, Shares.
Find narrows to lines containing the text. Follow keeps the newest line in
view (0.2.1's Auto-scroll switch did nothing). The newest 5,000 lines are kept.
"""

from __future__ import annotations

from collections import deque

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Select, Static

from forgekit import Toggle, glyph

KEEP = 5000
SHOW = [("Important", "important"), ("Everything", "all"), ("Problems", "problems"), ("Shares", "shares")]
STYLE = {"accepted": ("ok", "forge-ok"), "connected": ("ok", "forge-ok"), "rejected": ("warn", "forge-warn"),
         "problem": ("warn", "forge-warn"), "paused": ("warn", "forge-warn"), "resumed": ("ok", "forge-ok")}


class LogScreen(Vertical):
    BINDINGS = [Binding("slash", "find", "", show=False), Binding("f", "follow", "", show=False),
                Binding("c", "clear", "", show=False)]
    FORGE_HINTS = [("/", "find"), ("F", "follow on/off"), ("C", "clear"), ("1-4", "screens"), ("?", "all keys")]

    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.events: deque = deque(maxlen=KEEP)

    def compose(self) -> ComposeResult:
        yield Static("[b $forge-title-accent]Log[/]   [$forge-muted]what the miner says, newest at the bottom[/]",
                     classes="bf-group-title")
        with Horizontal(id="lg-bar"):
            yield Static("Show", classes="lg-label")
            show = Select(SHOW, value="important", allow_blank=False, id="lg-show")
            show.FORGE_HINTS = [("Enter", "open list"), ("Tab", "next")]
            yield show
            yield Static("Find", classes="lg-label")
            find = Input(placeholder="text to look for", id="lg-find")
            find.FORGE_HINTS = [("type", "to narrow"), ("Esc", "back"), ("Tab", "next")]
            yield find
            yield Toggle(True, on_label="Following", off_label="Not following", id="lg-follow")
        yield RichLog(id="lg-lines", max_lines=KEEP, wrap=True, markup=False, auto_scroll=True)
        with Horizontal(classes="forge-buttons lg-actions"):
            yield Button("Copy the log", id="lg-copy")
            yield Button("Clear", id="lg-clear")

    # ── lines ────────────────────────────────────────────────────────────────
    def wanted(self, e) -> bool:
        show = self.query_one("#lg-show", Select).value
        if show == "important" and e.kind in ("thread", "total"):
            return False
        if show == "problems" and e.kind not in ("problem", "rejected", "paused"):
            return False
        if show == "shares" and e.kind not in ("accepted", "rejected"):
            return False
        find = self.query_one("#lg-find", Input).value.strip().lower()
        return not find or find in e.text.lower()

    def line(self, e) -> Text:
        """One line, coloured with the theme's own colours (the log draws with
        Rich, which doesn't know forgekit's $forge-* names)."""
        colours = self.app.get_css_variables()
        mark, role = STYLE.get(e.kind, ("", "forge-text"))
        t = Text(f"{e.time}  ", style=colours.get("forge-muted", ""))
        t.append(f"{glyph(mark)} {e.text}" if mark else e.text, style=colours.get(role, ""))
        return t

    def add(self, e) -> None:
        self.events.append(e)
        if self.wanted(e):
            self.query_one(RichLog).write(self.line(e))

    def redraw(self) -> None:
        log = self.query_one(RichLog)
        log.clear()
        for e in self.events:
            if self.wanted(e):
                log.write(self.line(e))

    @on(Select.Changed, "#lg-show")
    @on(Input.Changed, "#lg-find")
    def _filter(self, e) -> None:
        e.stop()
        self.redraw()

    @on(Toggle.Changed, "#lg-follow")
    def _follow(self, e: Toggle.Changed) -> None:
        e.stop()
        log = self.query_one(RichLog)
        log.auto_scroll = bool(e.value)
        if e.value:
            log.scroll_end(animate=False)

    # ── keys and buttons ─────────────────────────────────────────────────────
    def action_find(self) -> None:
        self.query_one("#lg-find", Input).focus()

    def action_follow(self) -> None:
        t = self.query_one("#lg-follow", Toggle)
        t.set_value(not t.value)

    def action_clear(self) -> None:
        self.events.clear()
        self.query_one(RichLog).clear()
        self.app.notify("The log is cleared. The miner keeps running.")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        if e.button.id == "lg-copy":
            e.stop()
            text = "\n".join(f"{ev.time}  {ev.text}" for ev in self.events if self.wanted(ev))
            self.app.copy_to_clipboard(text)
            self.app.notify(f"{sum(1 for ev in self.events if self.wanted(ev))} lines copied.")
        elif e.button.id == "lg-clear":
            e.stop()
            self.action_clear()

    def on_key(self, e) -> None:
        if e.key == "escape" and self.query_one("#lg-find", Input).has_focus:
            e.stop()
            self.query_one(RichLog).focus()
