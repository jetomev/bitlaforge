# bitlaForge — full roadmap history

*The README carries the upcoming work and the two most recent releases; everything older lives here, newest-first.*

### v1.1.0 — October 8, 2026 — the same keys as every Forge app ([#13](https://github.com/jetomev/bitlaforge/issues/13))
- [x] Menu keys from forgekit 0.10.0: **1-5** and **Ctrl + the underlined letter** for every menu entry, Help included (5 opens Help); the bottom bar says "1-5 menu"
- [x] `--hypeforge` (hidden): a page of hypeForge Settings with no Quit of its own; Settings closes it, and bitlaForge asks first when the miner is running or a change isn't saved
- [x] Button labels in Javier's format, the key in brackets: **Start Mining (m)**, **Test Miner (t)**, **Save Changes (s)**, **Clear (c)**, **Stay (Esc)**
- [x] A rare error at closing fixed (the Dashboard's refresh firing while bitlaForge closed)
- [x] Tests 64 → 81, warnings 0

### v1.0.0 — October 2, 2026 — rebuilt, and safe ([#4](https://github.com/jetomev/bitlaforge/issues/4))
- [x] Rebuilt to match grubForge 2.0, from a screen-by-screen design Javier approved first
- [x] The miner never outlives bitlaForge ([#5](https://github.com/jetomev/bitlaforge/issues/5)); rejected shares counted ([#6](https://github.com/jetomev/bitlaforge/issues/6)); `name:port` pools connect ([#7](https://github.com/jetomev/bitlaforge/issues/7)); a broken settings file never saved over ([#8](https://github.com/jetomev/bitlaforge/issues/8))
- [x] Four screens (Dashboard, Settings, Log, History), real odds, pause when hot, the wallet checked offline, Bitcoin only, a manual inside the app
- [x] Every major distribution tested with its own miner

### v0.2.1 — August 9, 2026 — window polish
- [x] The Shortcuts window shows both ways to do something
- [x] `T` back as Test Miner; `Ctrl+H` opens Shortcuts
- [x] Windows hug their content, with a fixed footer for their buttons

### v0.2.0 — August 8, 2026 — the first Forge app on forgekit
- [x] The hand-built menus, header, footer and dialogs were replaced by the shared foundation — about 400 fewer lines while gaining the suite's look
- [x] Simplified to three sections, with real buttons on the Dashboard instead of a key legend
- [x] The old Setup screen became a read-only **Help → Install & Setup** window that checks your system fresh each time
- [x] Existing muscle memory kept working: `1-3`, `M`, `R`, `?`, `q`
- [x] The whole mining engine carried over unchanged

### v0.1.3 — May 29, 2026 — **first AUR release**
- [x] `testing/RELEASE-CHECKLIST.md` + v0.1.3 Test Matrix
- [x] Man page `bitlaforge.1`
- [x] PKGBUILD with hardened headless-mount `check()` + `PYTHONDONTWRITEBYTECODE=1` defenses
- [x] **Published on the AUR** — completes the Forge suite (joining grubForge, alacrittyForge, nogForge)

### v0.1.2 — May 29, 2026
- [x] System info on Setup screen (CPU model + logical/physical cores + load avg + memory) from stdlib
- [x] Config gains **miner name** (default hostname; also used as Stratum worker name) and **niceness** (0–19, default 19)
- [x] Threads input shows "of N available" hint from `os.cpu_count()`
- [x] `miner_runner` appends `wallet.workername` and wraps with `nice -n N`
- [x] Dashboard live tick (1s `set_interval` while mining) — uptime advances smoothly between hashmeter lines
- [x] Miner name surfaced in the Dashboard title
- [x] Live `minerd` CPU% / RAM from `/proc/<pid>/stat` + `/proc/<pid>/status` — makes the niceness setting observable
- [x] Hashrate parser hotfix: integer rates, per-thread aggregate, auto-scale to Mh/s / Gh/s

### v0.1.1 — May 28, 2026
- [x] Persist config to `~/.config/bitlaforge/config.toml` (TOML)
- [x] Wire `minerd` via `asyncio.create_subprocess_exec`: spawn, parse stdout, stop cleanly
- [x] Real Dashboard fields driven by parsed minerd output (hashrate / threads / accepted / rejected / uptime)
- [x] Stream minerd stdout into the Log screen's bounded buffer
- [x] Runtime `which("minerd")` check + Dashboard banner + friendly install guidance
- [x] Setup screen with AUR provider list + `minerd --version` self-test

### v0.1.0 — May 28, 2026
- [x] Pivot from Qt6/Widgets `BitLA` to Textual TUI under the Forge suite
- [x] Sidebar navigation + 3 screens (Dashboard, Log, Config)
- [x] `StatusMixin`, `HelpScreen`, `ConfirmDialog` ported from the Forge baseline
- [x] Catppuccin Mocha styling

---
