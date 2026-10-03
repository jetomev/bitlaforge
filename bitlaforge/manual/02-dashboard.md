# The Dashboard

Four boxes, refreshed every second.

## Mining

Whether the miner is running, for how long, and through which pool. If something stops mining from starting (no wallet yet, a settings file that can't be read, the miner not installed), it's said here, with the button that fixes it.

- **Start mining** / **Stop mining**, or press **M**.
- **Test the miner**, or press **T**: runs the miner for 10 seconds on one core with no pool, and says how fast one core is. Nothing is sent anywhere.

When the pool can't be reached, the box says so; the miner keeps trying every 30 seconds by itself.

## Speed

How many hashes (tries) per second this computer does, now and on average, with a small chart of the last 30 minutes (one bar per minute). **Cores** draws one bar per core, measured from zero, so equal bars mean the cores work equally.

Speed is shown in Mh/s: millions of tries per second.

## The lottery

Your real chance of finding a block today and this year, at your speed. See *The lottery, honestly*.

## Heat & load

- **Processor**: its temperature, from its own sensor, and when mining pauses for heat.
- **Miner uses**: how much of the processor the miner is using right now.
- **Priority**: Gentle or Normal (see *Miner*).
- **Shares**: work the pool accepted or rejected this session. A share is proof your computer is working; it isn't money. Only a found block pays.
