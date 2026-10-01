# bitlaForge — project rules

*How this project is built, tested and shipped. Written for the AI co-developer, and public on purpose: it is part of how the human + AI method is documented.*

## What it is
A [forgekit](https://github.com/jetomev/forgekit) (Python/Textual) terminal app for **solo** Bitcoin mining as the lottery it is: it wraps `minerd`, shows its state, and keeps its settings. Unlike the other Forge apps it drives a **long-running external process** (start/stop, stdout parsing, live dashboard); its only file is `~/.config/bitlaforge/config.toml` (user space, no `/etc`, no root).

## Non-negotiables
- **Built on forgekit.** The shell (menu bar, sections, dialogs, Help windows, console mode) is the kit's; bitlaForge adds only what makes it different. Do not re-implement or copy kit styling (the old copy of the form colours is K-1, bitlaforge#2).
- **Readable and usable on a plain text console (`TERM=linux`)** (forgekit#1): use the `$forge-*` colour roles in CSS and markup, and `glyph()` for marks. Console-check every release with forgekit's `tools/console-preview.py`.
- **The name is `bitlaForge`** (lowercase first letter, like `grubForge`, `alacrittyForge`). Older files still say `BitlaForge`: a known drift, fixed when they are touched, not in a sweep without Javier.
- **Fun, not profit.** The lottery framing stays honest; never promise earnings.
- **Credit, never comparison**, and the human + AI credit on every release artifact (PKGBUILD co-developer line, README, release body, man page).

## Code traps (from this repo's history)
- **Never name a method `_render`** in a Widget subclass: it shadows Textual's internal one and breaks rendering cryptically. Use `_redraw`.
- **Focus:** Textual focuses the first focusable widget in the whole DOM at start. Keep `DEFAULT_FOCUS` on containers, never an Input, or bare keys (1/2/3/M/T) get typed into fields. (bitlaforge#3: Esc does not yet leave a Config field.)
- **No double-wrapped workers:** `grep -rn "run_worker(self\.action_" bitlaforge/` must be empty.
- `minerd` is AUR-only, so it is an `optdepends`; the app degrades with `shutil.which("minerd")` and the Install & Setup window.

## How to run and test
- From source, on the kit in development: `PYTHONPATH=~/Programs/forgekit python main.py`. Installed: `bitlaforge`.
- Tests: **none committed yet** (a headless Pilot smoke suite was used in August and lives only in old scratchpads; committing a `tests/` folder is on TODO). Until then: the PKGBUILD `check()` mount, the matrix, and the audits below.
- Every release: `testing/RELEASE-CHECKLIST.md` top to bottom (snapshot `config.toml` first, audit greps, version sync), a Test Matrix and Test Results in `testing/` (`YYYYMMDD - Test Matrix for bitlaForge vX-Y-Z.md`), a console run, and **Javier's own test before anything builds on it**.
- Mining on real hardware before any release that touches `miner_runner.py`, the parser or the process lifecycle.

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
