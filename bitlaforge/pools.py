"""Solo pools, picked from a list (v1.0.0).

Only pools whose own page says they are solo mining are listed (checked
2 Oct 2026: solo.ckpool.org, "2% fee anonymous solo bitcoin mining", with its
Europe and Australia servers). Any other pool goes under "Other". An address
typed without ``stratum+tcp://`` gets it: the miner otherwise treats the pool
as a web server and never connects (F-4, bitlaforge#7).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Pool:
    url: str
    name: str
    where: str
    note: str = ""


POOLS = (
    Pool("stratum+tcp://solo.ckpool.org:3333", "solo.ckpool.org", "worldwide",
         "Solo mining, 2% fee if you find a block; no sign-up."),
    Pool("stratum+tcp://eusolo.ckpool.org:3333", "eusolo.ckpool.org", "Europe",
         "The same pool, from Europe: shorter distance from there."),
    Pool("stratum+tcp://ausolo.ckpool.org:3333", "ausolo.ckpool.org", "Australia",
         "The same pool, from Australia: shorter distance from there."),
)
DEFAULT = POOLS[0].url
SCHEMES = ("stratum+tcp://", "stratum+tcps://", "stratum+ssl://", "http://", "https://")


def normalise(address: str) -> str:
    """The address the miner should be given: spaces trimmed, and
    ``stratum+tcp://`` added when there is no scheme."""
    a = (address or "").strip()
    if a and not a.lower().startswith(SCHEMES):
        a = "stratum+tcp://" + a
    return a


def known(url: str) -> Pool | None:
    u = normalise(url).lower().rstrip("/")
    return next((p for p in POOLS if p.url == u), None)


def label(url: str) -> str:
    """How a pool is shown: its name and region, or the address itself."""
    p = known(url)
    if p:
        return f"{p.name} · {p.where}"
    return host(url) or "none"


def host(url: str) -> str:
    """host:port, without the scheme."""
    a = normalise(url)
    return a.split("://", 1)[-1].rstrip("/") if a else ""


def problem(url: str) -> str:
    """Plain words when an address can't work; empty when it can."""
    a = normalise(url)
    if not a:
        return "No pool yet: pick one from the list."
    rest = a.split("://", 1)[1]
    if not rest or any(c.isspace() for c in rest):
        return "This isn't a pool address: it looks like name:port, e.g. solo.ckpool.org:3333."
    hostpart, _, port = rest.rstrip("/").rpartition(":")
    if not hostpart or not port.isdigit() or not 0 < int(port) < 65536:
        return "The address needs a port at the end, e.g. solo.ckpool.org:3333."
    return ""
