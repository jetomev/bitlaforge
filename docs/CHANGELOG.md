# bitlaForge — full changelog

*The README carries the two most recent entries; the complete history lives here, newest-first.*

### v0.2.0 — August 8, 2026

**The forgekit adoption.** bitlaForge became the first Forge app to move onto the shared foundation, and the one that road-tested it.

The hand-rolled sidebar, header, footer, help screen and confirmation dialog — around 600 lines with their styling — were deleted. The menu bar, section switching, floating windows, theme and scrollbars all come from the shared library now.

A same-day review then simplified the app itself. The Dashboard's list of keyboard hints became real buttons: a two-state **Start / Stop Miner** whose label and colour follow the actual process, and **Test Miner**. The Setup screen stopped being a section and became a Help window, rebuilt each time it opens so it always reflects reality. A "Miner" menu was considered and cut — actions belong where the state is, not in a menu.

Everything that does the actual work carried over untouched: the miner process handling, statistics, system info, config storage, and the Log section. Your muscle memory kept working too.

Net result: 406 fewer lines, and it looks like the rest of the suite.

### v0.1.3 — May 29, 2026
**First AUR release — Forge release machinery.**

The version that gets bitlaForge into the AUR alongside its three Forge siblings. With this release, the **complete Forge suite** (grubForge + alacrittyForge + nogForge + bitlaForge) is now installable on Arch via a single `yay -S <name>`.

No code-feature changes vs. v0.1.2 — pure release machinery + packaging:

- **`testing/`** — `RELEASE-CHECKLIST.md` mirroring the grubForge / alacrittyForge discipline (pre-dogfood snapshot, async-worker audit, `_render` shadowing audit, version sync gate, doc coverage, co-author credit gate, release-day flow). Plus the v0.1.3 Test Matrix covering the full v0.1.0 → v0.1.3 user-facing surface for the first AUR-ship dogfood.
- **Man page `bitlaforge.1`** — full keybindings, safety section, dependency listing (`cpuminer` variants as optdeps), files, authors with co-developer credit.
- **PKGBUILD** — `depends=(python python-textual python-rich python-tomli-w)`; `optdepends=()` for the three `cpuminer*` AUR providers (since `minerd` is itself AUR-only and pacman can't reference AUR packages in `depends`); hardened `check()` runs the headless `run_test()` mount smoke under `PYTHONDONTWRITEBYTECODE=1` with defensive `__pycache__` cleanup in `package()` so we never ship the `.pyc` install-conflict class that bit grubForge v1.0.2.
- The two hotfixes from v0.1.2 (`cfe1010` CPU display + `e3e3091` hashrate parser) are folded forward into v0.1.3 — first tagged version that includes them.

Now installable as:
```bash
yay -S bitlaforge
```

### v0.1.2 — May 29, 2026
**Resource awareness + live Dashboard.**

v0.1.1 made bitlaForge mine; v0.1.2 makes it feel alive while doing it. Five per-group commits, all stdlib (no new deps):

- **G1 — System info on Setup.** New `bitlaforge/system_info.py` reads `/proc/cpuinfo`, `/proc/meminfo`, `os.getloadavg()`, and `os.cpu_count()` into a `SystemInfo` dataclass. The Setup screen gains a block above the minerd status showing **CPU model**, **logical/physical cores**, **memory total/available with % used**, and **1/5/15-minute load averages** color-graded against your core count (green when comfortably idle, yellow as load approaches your ceiling, red over it). Refreshes on **R**.
- **G2 — Config gains miner name + niceness + threads hint.** Two new fields in `~/.config/bitlaforge/config.toml`: `miner_name` (defaults to `socket.gethostname()`) and `niceness` (0–19, default 19). The Thread count label dynamically shows "of N available" sourced from the same `os.cpu_count()`. Forward-compatible: a v0.1.1 TOML loads cleanly with new defaults silently applied.
- **G3 — `miner_runner` worker name + nice wrapper.** `_build_args` now joins the sanitized `miner_name` to the wallet as `wallet.workername` (standard Stratum convention — pools show per-rig stats on their dashboards). `start()` wraps the spawn with `nice -n N` when niceness > 0; niceness ≤ 0 spawns directly with no overhead.
- **G4 — Dashboard live tick + name in header.** App installs a 1-second `set_interval` timer when the miner starts, cancels on stop (and when the parser sees the process end on its own). Each tick re-renders the Dashboard so **uptime advances smoothly** between minerd hashmeter dumps. The Dashboard title now shows the miner name in mauve: `⚡ BitlaForge — Miner Overview — workstation-rig`.
- **G5 — Live `minerd` CPU% / RAM from `/proc/<pid>/`.** New `process_stats.py` parses `/proc/<pid>/stat` (utime + stime ticks) and `/proc/<pid>/status` (VmRSS) — stdlib only, no `psutil`. The App tick captures a baseline at start, computes deltas on each tick, and writes `cpu_pct` (htop-style: 100% = one logical core) + `mem_mb` into `MinerStats`. Dashboard shows them under Performance. Makes the **niceness setting observable**: with niceness=19, you'll see minerd's CPU% drop the moment any other process needs cycles.

No dependency changes. Same `python`, `python-textual`, `python-rich`, `python-tomli-w`.

### v0.1.1 — May 28, 2026
**Make it actually mine.**

v0.1.0 shipped the Forge-style TUI skeleton with sidebar nav, three screens, the help modal, and a confirm dialog — but `minerd` integration was a stub: pressing M just flipped a state flag and notified. v0.1.1 turns the skeleton into a working tool. Four per-group commits:

- **G1 — Config persistence.** New `config_manager.py` (tomllib for read + tomli_w for write) saves pool / wallet / algorithm / threads to `~/.config/bitlaforge/config.toml`. The values survive launches; the Config screen loads them on `__init__`. Schema is intentionally flat so future cycles can add `[ui]` / `[log]` sections without breaking the miner section.
- **G2 — Real minerd subprocess.** New `miner_runner.py` with a `MinerRunner` class that uses `asyncio.create_subprocess_exec`, streams stdout line-by-line via a background `asyncio.Task`, and parses hashrate / accepted / rejected / threads out of pooler-cpuminer-format lines via regex. Each line is forwarded to the Log screen's bounded buffer; each parsed stat update repaints the Dashboard. Stop is `SIGTERM` with a 3-second grace, `SIGKILL` fallback. App's `M` binding is now async and wraps it all.
- **G3 — Runtime check + Dashboard banner + friendly guards.** `shutil.which("minerd")` runs at launch and on every M press. When the binary is missing, the Dashboard shows a persistent red "⚠ minerd not detected" banner with install hint; pressing M produces "install one of: cpuminer / cpuminer-multi / cpuminer-opt from AUR (`yay -S cpuminer`)" instead of the bare "binary not found" error.
- **G4 — Setup screen (4th nav).** New screen at **4** with the minerd status block (path if installed, or ✗ not installed), an "about minerd" explainer, the three AUR providers with copy-pasteable `yay -S` commands, the config file path, and a **T** action that runs `minerd --version` to verify the install actually works.

Dependency note: `python-tomli-w` is now required (same dep alacrittyForge already pulled in).

### v0.1.0 — May 28, 2026
**Pivot from Qt to TUI; first Forge-era release.**

Repo was originally `BitLA` — a Qt6/Widgets desktop scaffold pushed in November 2025 with simulation-driven UI and no real `minerd` integration. Untouched for ~6 months. Pivoted to a Textual TUI on 2026-05-28 because solo mining is fundamentally a streaming-stdout activity on long-running headless rigs, which a TUI fits better. The Qt code (~700 LOC of mostly scaffolding) is preserved permanently as the `v0.1.0-qt-archived` git tag.

Inaugural v0.1.0 ships the Forge-suite skeleton:

- Three screens (Dashboard, Log, Config) under sidebar navigation via `ContentSwitcher`.
- `StatusMixin` for unified status-line + toast feedback, with `popup=False` for passive mount-time hints (so the app launches quietly).
- Toggleable `HelpScreen` modal (Esc / q / ? dismiss; q shadows app-quit while help is up).
- `ConfirmDialog` with `escape` → cancel, `enter` → confirm.
- `DEFAULT_FOCUS` per screen so bindings fire on entry without a panel click.

`minerd` subprocess wiring is the v0.1.1 headline work.

---
