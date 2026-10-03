# Log and History

## Log

Press **3**. What the miner says, newest at the bottom, with times. The lines that matter are in plain words: **share accepted**, **share rejected** (and why), **connected**, **can't reach the pool**, **paused** and **going on** for heat.

- **Show**: *Important* (the default: everything but the per-core speed lines, which come every few seconds), *Everything*, *Problems*, or *Shares*.
- **Find** (or **/**): only lines containing the text. **Esc** leaves the field.
- **Following** (or **F**): keep the newest line in view. Turn it off to read back while the miner keeps writing.
- **Copy the log** copies what's shown; **Clear** (or **C**) empties it. The miner keeps running.

The newest 5,000 lines are kept while bitlaForge is open. Your wallet is never written in the Log.

## History

Press **4**. Every mining session, newest first: when it started, how long it ran, its average speed, its shares, and why it stopped (you stopped it, bitlaForge closed, the miner stopped by itself). Below the table: the totals since you started.

History lives in `~/.local/share/bitlaforge/history.json` and never leaves this computer. A session is written when it starts and brought up to date every minute, so if the computer is switched off while mining, the session still shows, as *bitlaForge closed unexpectedly*.
