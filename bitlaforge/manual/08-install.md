# Installing the miner

bitlaForge runs **minerd**, the program from the *cpuminer* project, which does the actual mining. It isn't installed with bitlaForge. Each way below was tested on 2 October 2026, in a fresh install of that distribution.

## KognogOS and Arch Linux

```
nog install cpuminer
```

(or `yay -S cpuminer` with any AUR helper).

## openSUSE Tumbleweed

openSUSE has it in its own collection:

```
sudo zypper install cpuminer
```

## Debian, Ubuntu and Fedora

These don't include the miner, so it comes from the cpuminer project's own release page on GitHub, which offers a ready-made program for 64-bit PCs. In a terminal, one line at a time:

```
curl -LO https://github.com/pooler/cpuminer/releases/download/v2.5.1/pooler-cpuminer-2.5.1-linux-x86_64.tar.gz
tar xzf pooler-cpuminer-2.5.1-linux-x86_64.tar.gz
sudo install -m 755 minerd /usr/local/bin/minerd
```

The first line downloads it, the second unpacks it, the third puts it where every program can find it (and asks for your password). If `curl` isn't installed: `sudo apt install curl` on Debian and Ubuntu.

## Then

Press **T** on the Dashboard to test it: 10 seconds on one core, nothing sent anywhere. bitlaForge looks for `minerd` each time you start mining or test, so there's no need to restart it after installing.
