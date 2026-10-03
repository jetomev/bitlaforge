"""Checking a Bitcoin address, here on this computer (v1.0.0).

A Bitcoin address carries its own check digits, so a typo is caught without
asking anyone: nothing is sent anywhere. Covers every kind of mainnet address:
``1…`` and ``3…`` (Base58Check), ``bc1q…`` (SegWit, BIP173 bech32) and
``bc1p…`` (Taproot, BIP350 bech32m). Testnet addresses are refused with
their own message, since a mainnet pool would never pay them.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BECH = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32, _BECH32M = 1, 0x2BC830A3


@dataclass(frozen=True)
class Check:
    ok: bool
    kind: str = ""        # "Taproot", "SegWit", "script", "legacy"
    problem: str = ""     # plain words when not ok


def _polymod(values: list[int]) -> int:
    gen = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    chk = 1
    for v in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if (top >> i) & 1 else 0
    return chk


def _expand(hrp: str) -> list[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _convertbits(data: list[int], frm: int, to: int) -> list[int] | None:
    acc = bits = 0
    out = []
    maxv = (1 << to) - 1
    for v in data:
        acc = (acc << frm) | v
        bits += frm
        while bits >= to:
            bits -= to
            out.append((acc >> bits) & maxv)
    if bits >= frm or ((acc << (to - bits)) & maxv):
        return None
    return out


def _segwit(addr: str) -> Check:
    if addr.lower() != addr and addr.upper() != addr:
        return Check(False, problem="Mixes capital and small letters; a real address uses one or the other.")
    a = addr.lower()
    pos = a.rfind("1")
    hrp, data = a[:pos], a[pos + 1:]
    if hrp in ("tb", "bcrt"):
        return Check(False, problem="This is a test-network address; it can't be paid real bitcoin.")
    if hrp != "bc" or len(a) > 90 or len(data) < 6:
        return Check(False, problem="Not a Bitcoin address.")
    if any(c not in _BECH for c in data):
        bad = next(c for c in data if c not in _BECH)
        return Check(False, problem=f"Has the character {bad!r}, which no bc1 address contains.")
    vals = [_BECH.index(c) for c in data]
    const = _polymod(_expand(hrp) + vals)
    if const not in (_BECH32, _BECH32M):
        return Check(False, problem="The check digits don't match: a character is mistyped or missing.")
    ver, prog = vals[0], _convertbits(vals[1:-6], 5, 8)
    if prog is None or ver > 16 or not 2 <= len(prog) <= 40:
        return Check(False, problem="Not a valid Bitcoin address.")
    if (ver == 0) != (const == _BECH32):
        return Check(False, problem="The check digits don't match: a character is mistyped or missing.")
    if ver == 0 and len(prog) not in (20, 32):
        return Check(False, problem="Not a valid Bitcoin address.")
    if ver == 1 and len(prog) == 32:
        return Check(True, "Taproot")
    if ver == 0:
        return Check(True, "SegWit")
    return Check(False, problem="A future kind of address that pools don't pay yet.")


def _base58(addr: str) -> Check:
    if any(c not in _B58 for c in addr):
        bad = next(c for c in addr if c not in _B58)
        return Check(False, problem=f"Has the character {bad!r}, which no Bitcoin address contains.")
    n = 0
    for c in addr:
        n = n * 58 + _B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    raw = b"\0" * (len(addr) - len(addr.lstrip("1"))) + raw
    if len(raw) != 25:
        return Check(False, problem="The wrong length for a Bitcoin address.")
    body, chk = raw[:-4], raw[-4:]
    if hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4] != chk:
        return Check(False, problem="The check digits don't match: a character is mistyped or missing.")
    if body[0] == 0:
        return Check(True, "legacy")
    if body[0] == 5:
        return Check(True, "script")
    if body[0] in (0x6F, 0xC4):
        return Check(False, problem="This is a test-network address; it can't be paid real bitcoin.")
    return Check(False, problem="Not a Bitcoin address.")


def check(address: str) -> Check:
    """Is this a Bitcoin address a pool can pay? Spaces around it are ignored."""
    a = (address or "").strip()
    if not a:
        return Check(False, problem="No wallet address yet: the pool needs one to pay a block to.")
    if any(c.isspace() for c in a):
        return Check(False, problem="Has a space in the middle; an address is one unbroken string.")
    if a.lower().startswith(("bc1", "tb1", "bcrt1")):
        return _segwit(a)
    if a[0] in "13mn2":
        return _base58(a)
    return Check(False, problem="Not a Bitcoin address: those start with bc1, 1 or 3.")


def short(address: str, width: int = 24) -> str:
    """An address shortened in the middle, for narrow places."""
    a = address.strip()
    if len(a) <= width:
        return a
    keep = (width - 1) // 2
    return f"{a[:keep]}…{a[-(width - 1 - keep):]}"
