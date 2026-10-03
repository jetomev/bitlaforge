# Pool & wallet

Settings ▸ **Pool & wallet**.

## Pool

A solo pool hands your computer the work to try and, if your computer finds a block, pays the reward to your wallet minus its fee. Solo means you aren't sharing: the whole block is yours, or nothing is.

The list holds the pools whose own page says they are solo mining:

- **solo.ckpool.org** (worldwide), **eusolo.ckpool.org** (Europe), **ausolo.ckpool.org** (Australia): the same pool from three places; 2% fee if you find a block; no sign-up.

**Other…** takes any pool's address, as `name:port` (for example `solo.ckpool.org:3333`). bitlaForge adds `stratum+tcp://` in front when it's missing; without it the miner would treat the pool as a website and never connect.

## Wallet

Your Bitcoin address: where a block's reward is paid. Every kind works: addresses starting with **bc1q** (SegWit), **bc1p** (Taproot), **1** or **3**.

The address is **checked here, on your computer**, as you type. A Bitcoin address carries its own check digits, so a mistyped or missing character is caught before it is ever used. Nothing is sent anywhere to check it. A wallet that doesn't pass can't be saved.

The Log never shows your wallet; it writes **WALLET** in its place.

## Worker name

A name for this computer, shown on the pool's page next to your wallet, so two computers mining to the same wallet can be told apart. Small letters, digits, `-` and `_`; anything else is left out.
