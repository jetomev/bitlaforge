# bitlaForge — project rules

*How this project is built, tested and shipped. Written for the AI co-developer, and public on purpose: it is part of how the human + AI method is documented.*

## What it is
A [forgekit](https://github.com/jetomev/forgekit) (Python/Textual) terminal app for **solo** Bitcoin mining as the lottery it is: it wraps `minerd`, shows its state, and keeps its settings. Unlike the other Forge apps it drives a **long-running external process** (start/stop, stdout parsing, live dashboard); its files are all the user's: `~/.config/bitlaforge/config.toml` (+ `backups/`), `~/.local/share/bitlaforge/history.json` and `logs/`, `~/.cache/bitlaforge/network.json` (no `/etc`, no root). Since 1.0 (Javier, 2 Oct 2026): four screens (Dashboard, Settings, Log, History), Bitcoin only, pause when hot, honest odds from mempool.space, and **the miner never outlives bitlaForge**.

## Non-negotiables
- **Built on forgekit.** The shell (menu bar, sections, dialogs, Help windows, console mode) is the kit's; bitlaForge adds only what makes it different. Do not re-implement or copy kit styling (0.2.x copied the form colours, K-1; removed in 1.0, which closed bitlaforge#2).
- **Readable and usable on a plain text console (`TERM=linux`)** (forgekit#1): use the `$forge-*` colour roles in CSS and markup, and `glyph()` for marks. Console-check every release with forgekit's `tools/console-preview.py`.
- **The name is `bitlaForge`** (lowercase first letter, like `grubForge`, `alacrittyForge`). 1.0 fixed it everywhere a person reads it; a test fails on `BitlaForge` in the code or manual (the class name `BitlaForgeApp` is code). Old `testing/` file names and quoted 0.x screen text keep it as history.
- **Mining is always the user's choice.** Never start it (in code, tests or a session) without Javier asking; tests and checks use a stand-in miner or `--benchmark`, and an unreachable pool (127.0.0.1:1).
- **Fun, not profit.** The lottery framing stays honest; never promise earnings.
- **Credit, never comparison**, and the human + AI credit on every release artifact (PKGBUILD co-developer line, README, release body, man page).

## Code traps (from this repo's history)
- **Never name a method `_render`** in a Widget subclass: it shadows Textual's internal one and breaks rendering cryptically. Use `_redraw`.
- **Focus:** Textual focuses the first focusable widget in the whole DOM at start. Keep focus off Inputs at start, or bare keys (1-4/M/T) get typed into fields. Esc leaves a field (F-1, #3, fixed in 1.0; tested).
- **The miner's process:** started behind `nice` and `setpriv --pdeathsig TERM`; check the program exists *before* spawning (behind the wrapper a missing one "starts" and ends at once). Pause = SIGSTOP; a paused miner gets SIGCONT before it is stopped. `on_unmount` and `cli.main`'s `finally` stop it whatever happens.
- **Rich vs forgekit colours:** `RichLog` draws with Rich, which doesn't know `$forge-*` names: look them up with `app.get_css_variables()`.
- **No double-wrapped workers:** `grep -rn "run_worker(self\.action_" bitlaforge/` must be empty.
- `minerd` is AUR-only on Arch (an `optdepends`), packaged on openSUSE, and **not packaged on Debian, Ubuntu or Fedora** (the cpuminer project's ready-made program works there; tested 2 Oct 2026). The app finds it with `shutil.which("minerd")` each time; without it the Dashboard points to the manual's *Installing the miner*.

## How to run and test
- From source, on the kit in development: `PYTHONPATH=~/Programs/forgekit python main.py`. Installed: `bitlaforge`.
- Tests: `PYTHONPATH=~/Programs/forgekit python -W default -m unittest discover tests` — **64 at 1.0.0, 0 warnings**; the count must never drop silently. A stand-in `minerd` (a script printing cpuminer's real lines) drives the lifecycle; `ps -C minerd` must be empty afterwards.
- Every distribution: `scripts/vm-distro-check.py` in the gf-* VMs. Test packages: `scripts/make-rc-packages.sh` (AUR recipe, rc suffix). Pictures: `docs/screenshots/generate.py`.
- Every release: `testing/RELEASE-CHECKLIST.md` top to bottom (snapshot `config.toml` first, audit greps, version sync), a Test Matrix and Test Results in `testing/` (`YYYYMMDD - Test Matrix for bitlaForge vX-Y-Z.md`), a console run, and **Javier's own test before anything builds on it**.
- Mining on real hardware (Javier's run) before any release that touches `miner.py`, the line reader or starting/stopping.

## Documentation, at every step
- `TODO.md` is updated after every step; it is the handoff between sessions.
- The README stays accurate top to bottom. Roadmap and changelog newest first; the README keeps upcoming work and the two newest releases, older ones live in `docs/ROADMAP.md` / `docs/CHANGELOG.md`.
- Findings are numbered F-n and each gets an issue, opened with a full explanation and closed with one.
- After every push: a Vault entry in `~/Google Drive/Rullynastre/BitlaForge/`.
- Plain words throughout. The readers are not engineers.

## Release discipline
- Version in **every** surface at once: `bitlaforge/__init__.py`, README badge, `bitlaforge.1` `.TH`, the AUR `PKGBUILD` + `.SRCINFO` in `~/Programs/aur-bitlaforge` (content in lockstep, not only `pkgver`).
- Signed commits with the co-author trailer; annotated signed tags (`git tag -s vX.Y.Z -m "…"`).
- Order: push `main` + tag → GitHub Release with notes and signed assets → AUR (packaging files only) → check with a fresh install (`pacman -Q`, not the helper's "done").
- `python-forgekit` must be on the AUR at the version bitlaForge needs **before** a bitlaForge release that depends on it.
