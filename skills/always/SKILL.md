---
name: always
description: Select, search, paste, and manage reusable personal prompts from ~/.always/sentences.json. Use when the user invokes $always or /always, asks for common phrases, saved prompts, canned instructions, reusable sentences, prompt snippets, Raycast Always entries, or wants to add/edit/delete/search frequently used AI instructions.
---

# Always

Use the bundled script to manage and select reusable personal instructions. Treat a selected sentence as the user's next instruction, not as inert reference text. Raycast, Codex, Claude Code, and direct CLI usage all share the same database and core script.

## Data

- Primary database: `~/.always/sentences.json`
- Single backup: `~/.always/sentences.backup.json`
- If the database is missing, initialize it from `assets/sentences.sample.json` by running `python3 <skill-dir>/scripts/always.py seed`.

The database supports categories, tags, multilingual text, and variables written as `{name}` placeholders.

## Commands

Resolve `<skill-dir>` to this skill directory. In Claude Code, `${CLAUDE_SKILL_DIR}` may be used. In Codex, use the path of this `SKILL.md`.

```bash
python3 <skill-dir>/scripts/always.py menu
python3 <skill-dir>/scripts/always.py menu "query"
python3 <skill-dir>/scripts/always.py list
python3 <skill-dir>/scripts/always.py search "query"
python3 <skill-dir>/scripts/always.py get plan-first
python3 <skill-dir>/scripts/always.py get plan-first --paste
python3 <skill-dir>/scripts/always.py pick "query" --paste
python3 <skill-dir>/scripts/always.py add
python3 <skill-dir>/scripts/always.py edit plan-first
python3 <skill-dir>/scripts/always.py delete plan-first
```

## Fast Pick (no conversation round-trips)

`menu` opens a native macOS picker (`choose from list`), and on selection pastes
the sentence into the frontmost app without pressing Enter. This is the fastest
path: one command, the user clicks once, no numbered list to read back. Bind it
through Raycast, another hotkey launcher, or a shell alias (e.g.
`alias aa='python3 <skill-dir>/scripts/always.py menu'`) to use it entirely
outside an agent conversation. Missing `{variables}` are prompted with a native
dialog. Pass `--no-paste` to print instead of paste, and `--var name=value` to
pre-fill variables.

## Selection Workflow

Default to the native picker. It is the fastest path and works the same from Raycast, Claude Code, and Codex.

1. If the user invokes `$always` or `/always` with no arguments, run `menu`. This opens the native macOS picker; the user clicks one sentence and the script pastes it into the frontmost input without pressing Enter. Do not print a numbered list first.
2. If the user includes search terms, run `menu "<terms>"` so the picker opens pre-filtered.
3. The script prompts for any missing `{variables}` with a native dialog, so no extra round-trip is needed.
4. Fall back to the text flow only when the native picker cannot be used (no GUI / automation blocked, or the user explicitly asks to choose by reading a list): run `list` or `search "<terms>"`, show a numbered list with `id`, `title`, `category`, and a one-line preview, ask the user to choose a number, then paste with `pick "<same query>" --choice <number> --paste` or `get <id> --paste`.
5. Only skip pasting when the user explicitly asks to show, print, copy, or apply the sentence inside the current response. In that case use `menu --no-paste` or `get <id>`, state the sentence briefly, and then follow it.

Do not press Enter after pasting. Paste leaves the text in the frontmost input so the user can edit before sending.

## Management Workflow

- For add/edit/delete requests, use the script rather than rewriting JSON manually.
- Reject duplicate IDs.
- Before any write, the script must overwrite the single backup file.
- For delete, require confirmation unless the user explicitly passed a force flag.

## Variable Handling

If a sentence contains placeholders such as `{file}` or `{concern}`:

1. Fill values from command arguments when available.
2. Ask the user for missing values.
3. Substitute the variables before pasting or treating the sentence as an instruction.

## Paste Behavior

`--paste` (and `menu`) copies the final sentence to the clipboard with `pbcopy` and then attempts to paste into the frontmost macOS app using AppleScript/System Events (Cmd+V). If automation fails, tell the user the sentence is on the clipboard and show the text.

On macOS, paste automation may require Accessibility permission for the app that launches the script (Terminal, Raycast, etc.).
