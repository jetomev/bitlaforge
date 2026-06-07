# BitlaForge release checklist

Pre-flight gates that any cut (alpha or stable) must pass before tag + GitHub release + AUR push. Mirrors the grubForge / alacrittyForge release discipline; adapted for BitlaForge's external-process scope (wraps `minerd`).

## Pre-dogfood snapshot

BitlaForge writes only to `~/.config/bitlaforge/config.toml` (user-space; no `/etc` writes). Snapshot it before testing so any change made during a dogfood pass is trivially reversible:

```sh
mkdir -p /tmp/bitlaforge-pretest
cp -p ~/.config/bitlaforge/config.toml /tmp/bitlaforge-pretest/ 2>/dev/null || true
sha256sum ~/.config/bitlaforge/config.toml > /tmp/bitlaforge-pretest/config.sha256 2>/dev/null || true
```

## External-process notes

- `minerd` is **not** in official Arch repos — only on the AUR (`cpuminer`, `cpuminer-multi`, `cpuminer-opt`). Pacman dependency arrays can only reference official-repo packages, so minerd lives in `optdepends=()`, not `depends=()`. BitlaForge degrades gracefully via runtime `shutil.which("minerd")` checks + the Setup screen.
- The headless mount smoke in PKGBUILD `check()` mounts the full Textual app under `run_test()` — it does NOT spawn `minerd` (no real mining at build time).
- A dogfood with mining-on-real-hardware should be run before any v0.x.y → v0.x.(y+1) transition that touches `miner_runner.py`, the parser, or the subprocess lifecycle.

## Async-worker pattern audit — `@work` and `run_worker` must not double-wrap

```sh
grep -rn "@work"      bitlaforge/
grep -rn "run_worker" bitlaforge/
grep -rn "run_worker(self\.action_" bitlaforge/   # MUST be empty
```

The third grep must return zero hits — a `run_worker(self.action_X())` where `action_X` is `@work`-decorated throws `WorkerError: Unsupported attempt to run an async worker` on newer Textual versions. (Background: this bug-class bit grubForge v1.0.0 in two screens.)

## `_render` shadowing audit (BitlaForge-specific)

```sh
grep -rn "def _render(self" bitlaforge/   # MUST be empty
```

Defining a `_render` method on any `Widget` subclass shadows Textual's internal `Widget._render()` and breaks the entire render pipeline with a cryptic `NoneType.render_strips` traceback. Always use `_redraw` instead. (Caught twice during BitlaForge v0.1.0 / v0.1.2; this audit makes the rule mechanical.)

## Version sync

Before tagging, all of these must agree on the version string:

- `bitlaforge/__init__.py` `__version__`
- `README.md` Version badge
- `bitlaforge.1` `.TH` header
- `~/Programs/aur-bitlaforge/PKGBUILD` `pkgver` + `pkgrel`
- AUR `.SRCINFO`

## Doc coverage

- README and man page must list every binding in `app.py` `BINDINGS` + every screen `BINDINGS` (excluding `show=False` aliases).
- `widgets/help_screen.py` must match the bindings actually defined. When a screen's `BINDINGS` changes, the help text changes with it.
- Setup screen's AUR provider list must mention every currently-recommended `minerd` provider.

## Co-author credit

Every release artifact must carry the human + AI credit:

- `~/Programs/aur-bitlaforge/PKGBUILD` co-developer line
- `README.md` Authors / Credits section
- GitHub release body
- Man page AUTHORS section

## Release-day flow

1. Pre-dogfood snapshot (above).
2. Run the Test Matrix top to bottom; log findings if any.
3. Land any hotfix batch closing in-scope findings (per-group commits, one release tag).
4. Audit greps (above).
5. Version sync (above).
6. Local `makepkg -f` smoke (runs `check()` headless mount).
7. `git tag vX.Y.Z` + `git push --tags`.
8. GitHub release with notes.
9. README sweep top to bottom (Description, Topics, README sections, Authors, Changelog).
10. Bump AUR PKGBUILD; `updpkgsums`; `makepkg --printsrcinfo > .SRCINFO`.
11. Local `sudo pacman -U` install smoke (or `makepkg -si`).
12. `git push` to `ssh://aur@aur.archlinux.org/bitlaforge.git`.
13. Verify public install path: `sudo pacman -R bitlaforge && yay -S bitlaforge` → smoke.
14. Refresh GitHub repo About + Topics + AUR badge in README.
15. Write end-of-day session log to vault with mandatory `## Next-session handoff (read this first)` section.
