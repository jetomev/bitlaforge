"""Shared status-feedback mixin for BitlaForge screens.

Ported from alacrittyForge v0.1.1's `StatusMixin` (which was itself ported
from grubForge v1.0.3's `widgets/status.py`). One `_set_status(msg, level,
popup=True)` that writes a colored icon + message to a per-screen status
line AND fires an app-level notify toast.

Pass `popup=False` for passive mount-time hints so screens don't spray
notifications at app launch (the lesson grubForge G1 captured after G3
landed; alacrittyForge ported the fix; BitlaForge starts with it built in).

Screens set `STATUS_WIDGET_ID` to the id of their status Label, or leave
it `None` (e.g. the Dashboard, which has no permanent status line — it
still gets the toast on actions like R or S).

Icons are the suite-canonical unicode set: ✓ (ok), ● (info), ⚠ (warn),
✗ (error). No ASCII drift, no markup at call sites — the mixin owns it.
"""

from __future__ import annotations

from textual.widgets import Label

# Catppuccin Mocha colors, keyed by status level.
_COLOR = {
    "ok":    "#a6e3a1",
    "info":  "#89b4fa",
    "warn":  "#f9e2af",
    "error": "#f38ba8",
}

_ICON = {
    "ok":    "✓",
    "info":  "●",
    "warn":  "⚠",
    "error": "✗",
}

_SEVERITY = {
    "ok":    "information",
    "info":  "information",
    "warn":  "warning",
    "error": "error",
}


class StatusMixin:
    """Provides a unified `_set_status(msg, level)` for screen widgets.

    Mix in *before* the Textual widget base so this `_set_status` is the
    one resolved, e.g. `class DashboardScreen(StatusMixin, Static)`.
    """

    # Override per screen with the id of its status Label, or leave None.
    STATUS_WIDGET_ID: str | None = None

    def _set_status(
        self,
        msg: str,
        level: str = "info",
        *,
        popup: bool = True,
    ) -> None:
        """Update the in-screen status line and (by default) fire a toast.

        Pass ``popup=False`` for passive mount-time hints so the screens
        don't spray notifications at app launch.
        """
        color = _COLOR.get(level, "#cdd6f4")
        icon = _ICON.get(level, "●")

        if self.STATUS_WIDGET_ID:
            try:
                self.query_one(f"#{self.STATUS_WIDGET_ID}", Label).update(
                    f"[{color}]{icon}  {msg}[/{color}]"
                )
            except Exception:
                pass

        if popup:
            self.app.notify(
                msg,
                severity=_SEVERITY.get(level, "information"),
                timeout=4,
            )
