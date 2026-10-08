# bitlaForge v1.1.0 — Test Matrix

Issue [#13](https://github.com/jetomev/bitlaforge/issues/13): the same keys as every Forge app (Javier, 8 Oct 2026), a page of hypeForge Settings (`--hypeforge`), and button labels as "Words in Title Case (k)" (Javier, 3 Oct 2026). Built on forgekit 0.10.0, which is not released yet: until it is, bitlaForge 1.1.0 runs **from the source folder**, on the forgekit in `~/Programs/forge-suite`.

## 1 · Built and checked by Claude (8 Oct 2026)

Automated: **81 tests** (64 before), all passing, 0 warnings (0 before); no miner left running afterwards. The 17 new ones are in `tests/test_v110.py`. Each fix was taken out once and its test seen to fail, then put back (17 checks):

- every underlined letter is different, and bitlaForge binds no number or menu Ctrl key of its own (forgekit makes them);
- 1-5 and Ctrl + letter reach every menu entry, Help included, Ctrl even from inside a field; the bottom bar says "1-5 menu";
- with `--hypeforge`: no Quit in the bar, Q and Ctrl+Q do nothing; Settings closing it while mining **asks first**, asked twice still shows one question, and "Stop Mining and Quit" leaves no miner running; with nothing running it closes at once; with a change not saved it asks;
- the option works as `--hypeforge` and `--hypeForge`, reaches the app, and is in neither `--help` nor the man page;
- every button label is in Title Case with its key in brackets, and the key really presses it (S in the review saves, once); the Mining box's buttons fit at 100 columns, mining or not;
- the 1-second Dashboard refresh firing while bitlaForge closes does no harm (an error the new tests found).

Text console (forgekit's `console-preview.py`, 100×30, with `--hypeforge`): Dashboard, Log and the Help menu: every character drawable and visible; no Quit in the bar; "1-5 menu" at the bottom. Screenshots regenerated.

## 2 · Javier's run (this desktop)

**Before you start**, copy your settings aside (nothing below should change them, but this is the rule):

```
cp -p ~/.config/bitlaforge/config.toml ~/.config/bitlaforge/config.toml.before-1.1.0
```

**How to start it** (from the source folder, on the new forgekit), in `~/Programs/bitlaforge`:

```
env PYTHONPATH=$HOME/Programs/forge-suite/forgekit python main.py
```

| ID | Do | Expect | Result |
|---|---|---|---|
| 2.1 | Start it (above) | The title says **bitlaForge 1.1.0**. The bottom bar says **M start / stop • T test • 1-5 menu • F1 help • ? all keys**. **Quit** is at the right of the menu bar | |
| 2.2 | Press **2**, **3**, **4**, **1** | Settings, Log, History, Dashboard, in that order | |
| 2.3 | Press **5** | The **Help** menu opens (Manual, Keys, License, About). **Esc** closes it | |
| 2.4 | Press **Ctrl+E**, **Ctrl+L**, **Ctrl+Y**, **Ctrl+D**, then **Ctrl+H** | Settings, Log, History, Dashboard; then the Help menu. **Esc** | |
| 2.5 | Press **2**, then **Tab** until you are in **Worker name** (the third field), type **12** at the end | The 12 is typed into the field; the screen doesn't change | |
| 2.6 | Still in the field, press **Ctrl+L** | The Log opens (Ctrl works from inside a field) | |
| 2.7 | Look at the bar above the bottom one | **1 change not saved yet**, with **Save Changes (s)** and **Discard Changes**. Click **Discard Changes** | |
| 2.8 | On the Log and on History, read the bottom bar | Both say **1-5 menu** | |
| 2.9 | Dashboard buttons | **Start Mining (m)** and **Test Miner (t)**, nothing cut off | |
| 2.10 | Log buttons (press **3**) | **Copy the Log** and **Clear (c)** | |
| 2.11 | Press **2**, pick the **Safety** group (↓ twice), change **Pause at** to another value, press **F10** | The review shows the change, with **Save (s)** and **Cancel (Esc)**. Press **Esc**, then **Discard Changes** | |
| 2.12 | Press **?** | The keys list: **1-5, Ctrl+letter** go to a menu entry, Help included; the Quit line says it's not there inside hypeForge Settings. **Esc** | |
| 2.13 | Press **Q** (nothing running, nothing changed) | bitlaForge closes at once; the closing note prints | |
| 2.14 | `env PYTHONPATH=$HOME/Programs/forge-suite/forgekit python main.py --version`, then the same with `--help` | **bitlaForge 1.1.0**; the help text says **1-5** and has **no** "hypeforge" in it | |

**As a page of hypeForge Settings**, started by hand with the hidden option:

```
env PYTHONPATH=$HOME/Programs/forge-suite/forgekit python main.py --hypeforge
```

| ID | Do | Expect | Result |
|---|---|---|---|
| 2.15 | Start it with `--hypeforge` (above) | **No Quit** in the menu bar; the bottom bar still says **1-5 menu** | |
| 2.16 | Press **Q**, then **Ctrl+Q** | Nothing happens. bitlaForge stays open | |
| 2.17 | Press **5** | The Help menu still opens. **Esc** | |
| 2.18 | **Real mining, your choice:** press **M** | Mining starts; the button now says **Stop Mining (m)** | |
| 2.19 | In a **second** terminal, the message hypeForge Settings sends when it closes a page: `kill -USR1 (pgrep -f "main.py --hypeforge")` | In bitlaForge: **Before you go · The miner is running**, with **Stop Mining and Quit** and **Stay (Esc)**. Mining continues for now | |
| 2.20 | With the question still showing, send the same command again | Nothing new: still one question. One **Esc** (Stay) closes it, and mining goes on | |
| 2.21 | Send the same command once more, and choose **Stop Mining and Quit** | bitlaForge closes; the closing note says **The miner is stopped** | |
| 2.22 | In the second terminal: `ps -C minerd` | Only the heading line: no miner left | |
| 2.23 | Start it with `--hypeforge` again (not mining), and send the same command | bitlaForge closes at once, no question | |
| 2.24 *(optional)* | On a text console (Ctrl+Alt+F3, log in, `cd ~/Programs/bitlaforge`, start it as in 2.1) | Everything readable; buttons show their keys; Ctrl+Alt+F1/F2 to come back | |

Then put your settings back only if something changed them:

```
cp -p ~/.config/bitlaforge/config.toml.before-1.1.0 ~/.config/bitlaforge/config.toml
```

**Later, at release:** once forgekit 0.10.0 and bitlaForge 1.1.0 are installed as packages, open bitlaForge from hypeForge Settings itself and repeat 2.15 to 2.22 there (Settings sends the close message itself).

Tell Claude "done": the History file, the backups, the run log and the settings file are read from the machine, and the results are written in `testing/20261008 - Test Results for bitlaForge v1-1-0.md`.
