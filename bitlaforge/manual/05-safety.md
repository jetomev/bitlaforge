# Safety

Settings ▸ **Safety**.

## Pause when hot

Mining keeps a processor fully busy for hours. With **Pause when hot** on (the default), bitlaForge checks the processor's temperature every 5 seconds. When it reaches **Pause at** (85 °C by default), the miner is paused: frozen in place, nothing lost. When the processor has cooled 5 °C, mining goes on by itself. Both are written in the Log.

Most processors are built to run up to about 95 °C; 85 °C keeps a margin. The temperature comes from the processor's own sensor (on AMD the one called Tctl, on Intel "Package"). If this computer has no sensor bitlaForge can read, the Dashboard says heat isn't watched.

## Lottery odds

With **Lottery odds** on (the default), bitlaForge asks **mempool.space**, a public Bitcoin website, once an hour for two things: how hard Bitcoin's puzzle is right now, and what the last block paid. **Nothing about you is sent**: no wallet, no speed. The answer is kept, so the odds still show when you're offline.

Turn it off and no internet is used for this; the Dashboard then doesn't show the odds.

## Saving

Every save shows each change, old → new, before anything is written; a copy of the settings file is made first (the newest 20 are kept in `~/.config/bitlaforge/backups/`); and the file is written in one step, so it's never left half-written. Anything else in the file, your own notes included, stays.

If the settings file can't be read (a typo made by hand, for example), bitlaForge **never saves over it**: the Dashboard says why, mining can't start, and **Restore the newest backup** puts the last good one back (the broken file is backed up first).
