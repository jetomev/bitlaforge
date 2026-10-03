#!/usr/bin/env bash
# Build a release-candidate package of bitlaforge from the current commit, for
# testing before a release (v1.0.0: Javier's run on the desktop, real mining).
# Adapted from alacrittyForge's script of the same name.
#
# The recipe is the AUR one (~/Programs/aur-bitlaforge/PKGBUILD), copied and
# changed in two places only: the source is a tarball of the current commit
# instead of the signed release asset (which doesn't exist yet), and the
# version gets an "rc" suffix (1.0.0rc1 sorts before 1.0.0, so the real
# release upgrades over it). check() and package() run exactly as on the AUR.
# The AUR folder itself is never changed. forgekit 0.5.1 is already released.
#
#   scripts/make-rc-packages.sh [rc-number]      (default 1)
#
# The package lands in dist-rc/. Logs to logs/make-rc-packages-<time>.log.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
log="logs/make-rc-packages-$(date +%Y%m%d-%H%M%S).log"
ln -sfn "$(basename "$log")" logs/make-rc-packages-latest.log
exec > >(tee "$log") 2>&1

rc="${1:-1}"
BF="$PWD"
OUT="$BF/dist-rc"
WORK="$(mktemp -d)"
trap 'rm -rf --one-file-system "$WORK"' EXIT
mkdir -p "$OUT"

base="$(sed -n 's/^__version__ = "\([0-9.]*\)".*/\1/p' bitlaforge/__init__.py)"
ver="${base}rc$rc"
echo "bitlaforge $ver from $(git log --format='%h %s' -1)"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "NOTE: uncommitted changes; the package is built from the last commit"
fi

python3 - ~/Programs/aur-bitlaforge/PKGBUILD "$WORK/PKGBUILD" "$ver" "$base" <<'PY'
import re, sys
src, out, ver, base = sys.argv[1:]
s = open(src).read()
s = re.sub(r"^pkgver=.*$", f"pkgver={ver}", s, flags=re.M)
s = re.sub(r"^pkgrel=.*$", "pkgrel=1", s, flags=re.M)
s = re.sub(r"^source=\(.*?\)$", f'source=("bitlaforge-{ver}.tar.gz")', s, flags=re.M | re.S)
s = re.sub(r"^sha256sums=\(.*?\)$", "sha256sums=('SKIP')   # local test build: not signed", s, flags=re.M | re.S)
s = re.sub(r"^validpgpkeys=\(.*?\)$", "", s, flags=re.M | re.S)
# the code says 1.0.0; the rc package is 1.0.0rcN
s = s.replace("assert __version__ == '${pkgver}', __version__",
              "assert __version__ == '${pkgver}'.split('rc')[0], __version__")
open(out, "w").write(s)
PY
git archive --format=tar.gz --prefix="bitlaforge-$ver/" -o "$WORK/bitlaforge-$ver.tar.gz" HEAD
(cd "$WORK" && makepkg -f --noconfirm 2>&1 | grep -vE '^\s+->|^  adding' )
cp "$WORK"/bitlaforge-"$ver"-*.pkg.tar.zst "$OUT/"
ls -la "$OUT"/bitlaforge-"$ver"-*.pkg.tar.zst
echo "OK: built bitlaforge $ver into dist-rc/"
