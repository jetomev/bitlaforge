# Keys

| Key | Does |
|---|---|
| **M** | start or stop mining |
| **T** | test the miner (10 seconds, one core, nothing sent) |
| **1 – 5**, or **Ctrl+D**, **Ctrl+S**, **Ctrl+L**, **Ctrl+I**, **Ctrl+H** | Dashboard, Settings, Log, History, and the Help menu (its number or Ctrl key again closes it) |
| **Tab** / **Shift+Tab** | next / previous field or button |
| **Enter** | open a list, press a button, confirm |
| **Space** | flip a switch |
| **↑ ↓** in a number | step through its presets |
| **F10** or **S** | save settings, with a review first |
| **R** | read the settings file again (your unsaved changes stay) |
| **F1** | help on what is selected |
| **/ F C** | in the Log: find, follow, clear |
| **?** | all keys |
| **Q** or **Ctrl+Q** | quit (stops the miner, after asking); not there inside hypeForge Settings |

Letter keys and numbers never act while you're typing in a field; **Esc** leaves the field. **Ctrl** + a letter works even inside a field.

Each menu entry's Ctrl letter is the underlined one: the first letter of its name, unless another entry already has it, then the next letter of its name. Help is always **H**, which is why History is **Ctrl+I**. On a plain text console (and some older terminals) **Ctrl+I** is the same key as **Tab**, so there **4** goes to History.

This manual (**Help ▸ Manual**, or **F1**), this keys list (**?**), **Help ▸ About** and **Help ▸ License** open as pages in the window, with Help lit at the top; **Esc** goes back to where you were. In the manual, **Backspace** goes back to the previous manual page.

Every button shows its key in brackets: **Start Mining (m)** is the same as pressing **M**, **Stay (Esc)** the same as **Esc**.

## Inside hypeForge Settings

hypeForge, the KognogOS desktop, shows bitlaForge as one page of its Settings window. It starts bitlaForge with a hidden option, `bitlaforge --hypeforge` (`--hypeForge` works too); you never need to type it.

On that page bitlaForge has **no Quit**: it isn't in the menu bar, and **Q** and **Ctrl+Q** do nothing. Settings closes it instead. If the miner is running, or a change isn't saved, bitlaForge **asks first**, exactly as its own Quit would; the miner still never outlives it.

## On a plain text console

bitlaForge works on a Linux text console (no desktop): colours and marks change to ones the console can draw, and the speed chart uses shaded blocks.
