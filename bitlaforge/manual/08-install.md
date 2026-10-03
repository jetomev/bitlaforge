# Installing the miner

bitlaForge runs **minerd**, the program from the *cpuminer* project, which does the actual mining. It isn't installed with bitlaForge.

## KognogOS and Arch Linux

```
nog install cpuminer
```

(or `yay -S cpuminer` with any AUR helper). Then press **T** on the Dashboard to test it.

bitlaForge looks for `minerd` each time you start mining, so there's no need to restart it after installing.
