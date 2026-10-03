"""Settings — a form like grubForge's, in three groups (v1.0.0).

Pool & wallet · Miner · Safety. The pool is picked from a list (Other takes
any address); the wallet is checked as it is typed, on this computer; the
rest are presets and switches. Nothing is written until Save (F10), which
shows every change first and makes a backup.
"""

from __future__ import annotations

from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import ContentSwitcher, Input, OptionList, Select, Static
from textual.widgets.option_list import Option

from forgekit import Choices, FilterPicker, Notice, NumberPresets, SettingRow, Toggle, glyph

from .. import pools
from ..settings import BY_KEY, GENTLE, GROUPS, NORMAL, SETTINGS, Setting, words
from ..wallet import check

OTHER = "__other__"
SELECT_HINTS = [("Enter", "open list"), ("Tab", "next"), ("F1", "help")]


def wallet_line(address: str) -> str:
    if not address:
        return "[$forge-muted]Your Bitcoin address. Checked here; nothing is sent anywhere.[/]"
    c = check(address)
    if c.ok:
        return (f"[$forge-ok]{glyph('ok')} a valid Bitcoin address[/] [$forge-muted]({c.kind}) "
                f"{glyph('dash')} checked here, nothing is sent anywhere[/]")
    return f"[$forge-warn]{glyph('warn')} {escape(c.problem)}[/]"


class SettingsScreen(Horizontal):
    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.rows: dict[str, SettingRow] = {}

    @property
    def config(self):
        return self.app.config

    # ── the pool list ────────────────────────────────────────────────────────
    def pool_options(self) -> list[tuple[str, str]]:
        """(label, value) for the pool Select: the known pools, the current
        address when it isn't one of them, then Other."""
        cur = self.config.value("pool")
        opts = [(f"{p.name} {glyph('dash')} {p.where}", p.url) for p in pools.POOLS]
        if cur and not pools.known(cur):
            opts.insert(0, (f"{pools.host(cur)} (yours)", cur))
        opts.append((f"Other{glyph('ellipsis')}", OTHER))
        return opts

    # ── building the form ────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        groups = OptionList(*(Option(label, id=gid) for gid, label, _d in GROUPS), id="bf-groups")
        groups.FORGE_HINTS = [("↑↓", "choose a group"), ("Tab", "its settings"), ("F10", "save"), ("?", "all keys")]
        yield groups
        with Vertical(id="bf-settings-right"):
            if not self.config.readable:
                yield Notice("Your settings file can't be read, so nothing can be changed here",
                             [escape(self.config.error),
                              "The Dashboard offers the newest backup; or fix the line and press R."],
                             level="warn", id="bf-readonly")
            with ContentSwitcher(initial=f"grp-{GROUPS[0][0]}", id="bf-groupforms"):
                for gid, label, desc in GROUPS:
                    with VerticalScroll(id=f"grp-{gid}", classes="bf-group", can_focus=False):
                        yield Static(f"[b $forge-title-accent]{label}[/]   [$forge-muted]{escape(desc)}[/]",
                                     classes="bf-group-title")
                        for s in SETTINGS:
                            if s.group == gid:
                                row = self._row(s)
                                self.rows[s.key] = row
                                yield row
            yield Static("", id="bf-about")

    def _row(self, s: Setting) -> SettingRow:
        disabled = not self.config.readable
        v = self.config.value(s.key)
        note = s.note
        if s.control == "pool":
            ctrl = Select(self.pool_options(), value=v, allow_blank=False, disabled=disabled)
            ctrl.FORGE_HINTS = SELECT_HINTS
            note = v
        elif s.control == "wallet":
            ctrl = Input(v, placeholder="bc1…", disabled=disabled, max_length=100)
            ctrl.FORGE_HINTS = [("type", "or paste your address"), ("Tab", "next"), ("F1", "help")]
        elif s.control == "text":
            ctrl = Input(v, disabled=disabled, max_length=32)
            ctrl.FORGE_HINTS = [("type", "a name"), ("Tab", "next"), ("F1", "help")]
        elif s.control == "number":
            ctrl = NumberPresets(v, [(str(p), p) for p in s.presets], unit=s.unit, minimum=s.lo, maximum=s.hi,
                                 disabled=disabled)
        elif s.control == "priority":
            ctrl = Choices([(str(GENTLE), "Gentle"), (str(NORMAL), "Normal")], str(v), disabled=disabled)
        else:
            ctrl = Toggle(bool(v), disabled=disabled)
        ctrl.setting_key = s.key
        row = SettingRow(s.label, ctrl, note=note, help=s.help, setting=s.key, id=f"row-{s.key}")
        return row

    def on_mount(self) -> None:
        self.query_one("#bf-groups", OptionList).highlighted = 0
        self.query_one("#row-wallet").mount(Static(wallet_line(self.config.value("wallet")), id="bf-wallet-check"))
        self.sync()

    # ── moving around ────────────────────────────────────────────────────────
    @on(OptionList.OptionHighlighted, "#bf-groups")
    def _group(self, e: OptionList.OptionHighlighted) -> None:
        self.query_one("#bf-groupforms", ContentSwitcher).current = f"grp-{e.option.id}"

    def on_key(self, e) -> None:
        # Esc leaves a field, back to the group list (F-1, bitlaforge#3)
        if e.key == "escape" and isinstance(self.app.focused, Input):
            e.stop()
            self.query_one("#bf-groups", OptionList).focus()

    def show_group(self, gid: str) -> None:
        self.query_one("#bf-groups", OptionList).highlighted = [g for g, _l, _d in GROUPS].index(gid)

    def focus_setting(self, key: str) -> None:
        self.show_group(BY_KEY[key].group)
        self.rows[key].control.focus()

    def on_descendant_focus(self, e) -> None:
        row = next((a for a in e.widget.ancestors_with_self if isinstance(a, SettingRow)), None)
        about = self.query_one("#bf-about", Static)
        if row is None:
            about.update("")
            return
        s = BY_KEY[row.setting]
        default = "this computer's name" if s.key == "miner_name" else words(s.key, s.default)
        about.update(f"[$forge-muted]{'─' * 3} About this setting {'─' * 40}[/]\n{escape(s.help)}\n"
                     f"[$forge-muted]Default: {escape(default)}  {glyph('dash')}  F1 opens the manual[/]")

    # ── changes ──────────────────────────────────────────────────────────────
    def _stage(self, key: str, value) -> None:
        self.config.set(key, value)
        self._mark(key)
        if key == "wallet":
            self.query_one("#bf-wallet-check", Static).update(wallet_line(self.config.value("wallet")))
        self.app.refresh_state()

    def _mark(self, key: str) -> None:
        row = self.rows[key]
        if key in self.config.pending:
            row.mark_changed(words(key, self.config.original(key)))
        else:
            row.mark_unchanged()
        if key == "pool":
            note = row.query_one(".forge-setting-note", Static)
            if key not in self.config.pending:
                note.update(f"[$forge-muted]{escape(self.config.value('pool'))}[/]")

    @on(NumberPresets.Changed)
    def _number(self, e: NumberPresets.Changed) -> None:
        if (key := getattr(e.number, "setting_key", None)):
            e.stop()
            self._stage(key, int(e.value))

    @on(Toggle.Changed)
    def _toggle(self, e: Toggle.Changed) -> None:
        if (key := getattr(e.toggle, "setting_key", None)):
            e.stop()
            self._stage(key, bool(e.value))

    @on(Choices.Changed)
    def _choices(self, e: Choices.Changed) -> None:
        if (key := getattr(e.choices, "setting_key", None)):
            e.stop()
            self._stage(key, int(e.value))

    @on(Input.Changed)
    def _text(self, e: Input.Changed) -> None:
        if (key := getattr(e.input, "setting_key", None)):
            e.stop()
            value = e.value.strip()
            if key == "miner_name" and not value:
                value = BY_KEY[key].default or self.config.original(key)
            self._stage(key, value)

    @on(Select.Changed)
    def _select(self, e: Select.Changed) -> None:
        if getattr(e.select, "setting_key", None) != "pool":
            return
        e.stop()
        if e.value == OTHER:
            self._other_pool(e.select)
            return
        self._stage("pool", e.value)

    def _other_pool(self, select: Select) -> None:
        def done(value: str | None) -> None:
            if value:
                why = pools.problem(value)
                if why:
                    self.app.notify(why, title="That pool address can't work", severity="warning", timeout=8)
                    value = None
            if not value:
                with select.prevent(Select.Changed):
                    select.value = self.config.value("pool")
                return
            self._stage("pool", pools.normalise(value))
            with select.prevent(Select.Changed):
                select.set_options(self.pool_options())
                select.value = self.config.value("pool")

        hosts = [pools.host(p.url) for p in pools.POOLS]
        self.app.push_screen(FilterPicker(
            "Another pool", hosts, current=pools.host(self.config.value("pool")), allow_custom=True,
            hint="Type the pool's address as name:port (e.g. solo.ckpool.org:3333)"), done)

    # ── after save / discard / reload ────────────────────────────────────────
    def sync(self) -> None:
        """Put every control back to the settings' values and marks."""
        for key, row in self.rows.items():
            ctrl, v = row.control, self.config.value(key)
            if isinstance(ctrl, Select):
                with ctrl.prevent(Select.Changed):
                    ctrl.set_options(self.pool_options())
                    ctrl.value = v
            elif isinstance(ctrl, Toggle):
                ctrl.set_value(bool(v), announce=False)
            elif isinstance(ctrl, NumberPresets):
                ctrl.set_value(v, announce=False)
            elif isinstance(ctrl, Choices):
                ctrl.set_value(str(v), announce=False)
            elif isinstance(ctrl, Input):
                with ctrl.prevent(Input.Changed):
                    ctrl.value = v
                if not ctrl.has_focus:
                    ctrl.cursor_position = 0
            ctrl.disabled = not self.config.readable
            self._mark(key)
        try:
            self.query_one("#bf-wallet-check", Static).update(wallet_line(self.config.value("wallet")))
        except Exception:
            pass
