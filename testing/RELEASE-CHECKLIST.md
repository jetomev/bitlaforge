# bitlaForge release checklist

Gates every release must pass before the tag, the GitHub release and the AUR push. Mirrors grubForge's and alacrittyForge's; adapted for what bitlaForge does differently: it runs a long-lived program (`minerd`).

## Before any test on this desktop

bitlaForge writes only user files. Copy them aside first, so anything a test changes can be put back:

```sh
cp -p ~/.config/bitlaforge/config.toml ~/.config/bitlaforge/config.toml.before-X.Y.Z
```

History (`~/.local/share/bitlaforge/history.json`) and backups (`~/.config/bitlaforge/backups/`) only grow; nothing needs saving there.

## Tests and warnings

```sh
PYTHONPATH=~/Programs/forgekit python -W default -m unittest discover tests
```

All pass, **report the count** (1.0.0: 64) and the warnings (1.0.0: 0). A drop in the count means a test was deleted silently. The AUR `check()` runs the same tests.

## Every distribution

`scripts/vm-distro-check.py` in the gf-* VMs (snapshot `fresh`), as in the 1.0.0 matrix §5: PASS on Debian, Ubuntu, Fedora and openSUSE. Debian/Ubuntu/Fedora need the cpuminer project's ready-made program first (the manual's *Installing the miner*); openSUSE `zypper install cpuminer`.

## The miner (any release touching `miner.py`, the reader, or starting/stopping)

- The miner's lines in `tests/test_miner.py` (`REAL`) are cpuminer's own; if a new cpuminer changes its wording, capture fresh lines first (`minerd --benchmark`, an unreachable pool), never guess.
- After every headless run: `ps -C minerd -o pid --no-headers` must be empty.
- Real mining on real hardware before the release (Javier's run).

## Audits

```sh
grep -rn "run_worker(self\.action_" bitlaforge/   # MUST be empty (double-wrapped workers)
grep -rn "def _render(self" bitlaforge/          # MUST be empty (shadows Textual's own)
grep -rn "#[0-9a-fA-F]\{6\}" bitlaforge/ui bitlaforge/app.py   # MUST be empty: colours only through $forge-* roles
```

## Text console and 100 columns

forgekit's `tools/console-preview.py --size 100x30` on all four screens: every character in the console font, every letter visible. The `*_100_columns_*` test covers widths.

## Version sync

All of these say the same version:

- `bitlaforge/__init__.py` `__version__`
- `README.md` Version badge (and, after the AUR push, the AUR badge's `?v=` cache-buster)
- `bitlaforge.1` `.TH` header
- `~/Programs/aur-bitlaforge/PKGBUILD` `pkgver` + `pkgrel`, and `.SRCINFO` (`makepkg --printsrcinfo | diff - .SRCINFO`)

## Documentation

- README top to bottom; roadmap and changelog newest first, the README keeping upcoming work and the two newest releases.
- The man page and the manual (`bitlaforge/manual/`) list every key in `app.py` `BINDINGS`, `SHORTCUTS` and the Log's keys.
- The manual's *Installing the miner* only carries ways tested in a fresh install.
- Screenshots: `python docs/screenshots/generate.py` (a stand-in miner, an example wallet; never Javier's).

## Credit

The human + AI credit on every release artifact: the PKGBUILD co-developer line, the README Authors, the GitHub release body, the man page AUTHORS, and the co-author trailer on every commit.

## Release-day order

1. Test Matrix and Results in `testing/` (`YYYYMMDD - Test Matrix for bitlaForge vX-Y-Z.md`); Javier's run.
2. Tests, audits, console, version sync (above).
3. Docs commit `docs: README + version bump for vX.Y.Z`; signed annotated tag; push `main` + tag.
4. Signed release archive (`git archive` + `gpg --detach-sign --armor`); GitHub release with notes and a picture, Latest; download it back and `cmp`.
5. AUR: `pkgver`, `sha256sums`, `.SRCINFO`; pre-flight (checksum, `gpg --verify`, `.SRCINFO` diff); build from the GitHub download; push (`SSH_AUTH_SOCK=/tmp/aur-agent.sock`); the AUR shows the version.
6. README AUR badge cache-buster; check what GitHub serves.
7. Close the release's issues with a full explanation; GitHub About and topics.
8. Install the public package (`nog install bitlaforge`), `pacman -Q`.
9. Memory, TODO, Vault.
