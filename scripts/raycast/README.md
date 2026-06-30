# Always Raycast Commands

This directory contains Raycast Script Commands that make Always usable from a
global shortcut while keeping all real logic in the Always core CLI.

## Commands

| Script | Raycast title | What it does |
|---|---|---|
| `always.sh` | `Always` | Opens the native Always picker and pastes the selected sentence into the frontmost app. |
| `open-json.sh` | `Always: Open JSON` | Opens the live database at `~/.always/sentences.json` in the default editor. |

Both commands resolve the repository path relative to this directory, so they do
not depend on an absolute checkout path. Python must be 3.10 or newer and is
resolved in this order:

1. `ALWAYS_PYTHON`, when set to an executable path.
2. `python3` from Raycast's environment.
3. Common macOS Python locations: `/opt/homebrew/bin/python3`,
   `/usr/local/bin/python3`, `/usr/bin/python3`.

## Setup

1. Run the normal Always installer from the repository root:

   ```bash
   scripts/install.sh
   ```

2. In Raycast, open **Settings → Extensions → Scripts**.
3. Add this directory as a Script Directory:

   ```text
   <repo>/scripts/raycast
   ```

4. Assign a global hotkey to `Always`. The recommended shortcut is double
   Option (`⌥⌥`) because it is fast and does not conflict with common app
   shortcuts.

Raycast launches these scripts directly. The scripts call
`skills/always/scripts/always.py`, which still owns the database, search,
variable rendering, backup, and paste behavior.

Direct JSON edits bypass the CLI's rolling backup and validation. Use the JSON
command for quick inspection or controlled bulk cleanup; prefer the CLI `add`,
`edit`, and `delete` commands for routine changes.

## Raycast references

- Script Commands: <https://manual.raycast.com/script-commands>
- Command aliases and hotkeys: <https://manual.raycast.com/command-aliases-and-hotkeys>
