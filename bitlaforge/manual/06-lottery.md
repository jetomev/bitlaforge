# The lottery, honestly

Every try your computer makes has a fixed, tiny chance of completing a Bitcoin block: one in (difficulty × 4,294,967,296). The difficulty is set by the whole network, and on 2 October 2026 the network did about **975 million million million** tries per second.

At 184 Mh/s (a 16-core desktop), that's a chance of about **1 in 36 billion per day**, or **1 in 98 million per year**. The Dashboard shows yours, worked out from your own speed and the latest numbers from mempool.space.

The chance is the same every second: there's no progress, no "getting closer". A session that ends doesn't lose anything, and a long one doesn't build anything up.

## What shares are

The pool also sends easier puzzles. Solving one is a **share**: proof your computer is working. Shares are counted on the Dashboard and in History, but **they aren't money**. Only a found block pays.

A **rejected** share is one the pool said no to, usually because the work was already out of date when it arrived (someone else found a block a moment before). A few are normal.

## If you find a block

The miner can't tell: the pool can. Your wallet's page on the pool shows it (for ckpool: open `solo.ckpool.org` in a browser and enter your address). The reward arrives in your wallet after 100 more blocks, about 17 hours.
