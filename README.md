<div align="center">

# Always

[English](README.md) | [中文](README.zh.md)

> *Your best instructions should not have to be rewritten in every conversation.*

**A shared personal sentence picker for Codex and Claude Code.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](#requirements) [![Claude Code](https://img.shields.io/badge/Claude%20Code-supported-blue?logo=claude&logoColor=white)](https://code.claude.com/docs/en/skills) [![Codex](https://img.shields.io/badge/Codex-supported-10a37f?logo=openai&logoColor=white)](https://developers.openai.com/codex/skills) [![macOS](https://img.shields.io/badge/macOS-native%20picker-000000?logo=apple&logoColor=white)](#native-picker-and-paste)

**One `~/.always/sentences.json` file gives both agents the same reusable prompts, writing preferences, review instructions, and parameterized templates.**

[Quick start](#30-second-quick-start) · [Daily usage](#daily-usage) · [Manage sentences](#manage-your-library) · [CLI reference](#cli-reference) · [Design details](PROJECT_DETAILS.md) · [Safety](#privacy--safety)

</div>

---

Good instructions are often repeated: plan before coding, review a particular file, answer in a specific tone, verify before finishing. Always stores those instructions once and makes them available to both Codex and Claude Code. Pick a sentence, fill any variables, edit it if needed, and send it yourself.

## How It Works

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/architecture-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/architecture-light.svg">
  <img alt="Always architecture: Codex and Claude Code share one personal sentence database and use the same picker script." src="assets/architecture-light.svg">
</picture>

The repository contains the skill and its CLI. The installer exposes that same skill directory to both agents with symlinks. Your live content stays outside the repository in `~/.always/sentences.json`, so updating the code does not overwrite your personal library.

## 30-Second Quick Start

```bash
git clone https://github.com/ycl-2004/Always.git
cd Always
scripts/install.sh
```

Then open Codex and type:

```text
$always
```

In Claude Code, use:

```text
/always
```

On macOS, a native picker opens. Choose a sentence and Always pastes it into the frontmost input without pressing Enter. You remain in control: edit the result, then send it yourself.

> [!NOTE]
> The native picker and automatic paste require macOS. Listing, searching, printing, and managing sentences use the Python CLI and do not require GUI automation.

## What You Get

- One personal sentence library shared by Codex and Claude Code.
- A native macOS picker with optional pre-filtering.
- Categories, tags, multilingual text, and `{variable}` placeholders.
- CLI commands for listing, searching, selecting, adding, editing, and deleting.
- A one-generation backup before every managed write.
- No cloud service, account, API key, or runtime package installation.

## Install

Run the installer from a source checkout:

```bash
scripts/install.sh
```

It creates these links:

```text
~/.agents/skills/always  -> <repo>/skills/always
~/.claude/skills/always -> <repo>/skills/always
```

It also creates the live database from the bundled sample only when the database does not already exist:

```text
~/.always/sentences.json
```

Existing non-symlink skill directories are never replaced automatically. Move or remove the conflicting directory yourself, then rerun the installer.

### Updating Always

Because both agent paths point to the source checkout, update that checkout:

```bash
git pull --ff-only
```

Your personal database is not stored in the repository and is not replaced by a normal update.

### Uninstalling

Remove the two skill links:

```bash
rm ~/.agents/skills/always
rm ~/.claude/skills/always
```

Your personal library remains at `~/.always/`. Delete it separately only if you intentionally want to remove your saved content.

## Daily Usage

| Action | Codex / Claude instruction | Result |
|---|---|---|
| Open all sentences | `$always` / `/always` | Opens the native picker and pastes the selection. |
| Filter first | `$always review` | Opens the picker with matching entries only. |
| List without pasting | `$always list my saved sentences` | Prints a readable list. |
| Add an entry | `$always add a reusable instruction …` | Writes a new database entry. |
| Edit an entry | `$always edit chinese-human-tone …` | Updates the entry by ID. |
| Delete an entry | `$always delete explain-simply` | Requests confirmation, then deletes it. |

The exact invocation UI can vary by client. The skill ID is always `always`.

## Native Picker and Paste

The fastest path is:

```bash
python3 skills/always/scripts/always.py menu
```

The flow is deliberately non-destructive:

1. AppleScript opens a native `choose from list` dialog.
2. Missing `{variables}` are collected in native dialogs.
3. The rendered sentence is copied with `pbcopy`.
4. System Events sends `Cmd+V` to the frontmost app.
5. Enter is never pressed; the user reviews and sends the text.

macOS may require Accessibility permission for Terminal, Raycast, Codex, or whichever app launches the script. If paste automation fails, the sentence remains on the clipboard and the CLI prints it.

## Manage Your Library

The supported path is the CLI or an agent using the CLI. Direct JSON edits are possible but bypass backup and validation behavior.

### List and search

```bash
python3 skills/always/scripts/always.py list
python3 skills/always/scripts/always.py search "review risk"
```

Search is case-insensitive and checks ID, title, text, category, language, and tags. Multiple query terms use AND matching; this is substring filtering, not fuzzy ranking.

### Add

Interactive:

```bash
python3 skills/always/scripts/always.py add
```

Non-interactive:

```bash
python3 skills/always/scripts/always.py add \
  --id analyze-first \
  --title "Analyze first" \
  --text "Inspect the relevant files and constraints before making changes." \
  --category planning \
  --language en \
  --tag analysis \
  --tag context
```

IDs are normalized to lowercase ASCII slugs and must be unique. When the title is not Latin text, provide an explicit ASCII `--id`.

### Edit

```bash
python3 skills/always/scripts/always.py edit analyze-first
```

Press Enter at an interactive prompt to preserve its current value. Passing one or more `--tag` flags replaces the existing tag list.

### Delete

```bash
python3 skills/always/scripts/always.py delete analyze-first
```

Deletion requires typing `yes`. `--force` skips confirmation and should be reserved for controlled automation.

## Variables

Placeholders use Python-style braces:

```text
Review {file} carefully. Focus on {concern}.
```

The native menu prompts for missing values. CLI values can be supplied explicitly:

```bash
python3 skills/always/scripts/always.py get review-focus \
  --var "file=README.md" \
  --var "concern=installation accuracy" \
  --paste
```

## CLI Reference

| Command | Purpose |
|---|---|
| `seed` | Create the database from sample data; `--force` resets an existing database after backup. |
| `list [query]` | List all entries or entries matching an optional query. |
| `search [query]` | Search across all supported fields. |
| `get <id>` | Print or paste one entry by exact ID. |
| `pick [query]` | Search, choose by number, then print or paste. |
| `menu [query]` | Open the native macOS picker; pastes by default. |
| `add` | Add an entry interactively or with flags. |
| `edit <id>` | Edit or rename an existing entry. |
| `delete <id>` | Delete an entry after confirmation. |

Run command-specific help when needed:

```bash
python3 skills/always/scripts/always.py menu --help
python3 skills/always/scripts/always.py edit --help
```

## Data Model

The live database is:

```text
~/.always/sentences.json
```

Each entry contains:

```json
{
  "id": "review-focus",
  "title": "Review with focus",
  "text": "Review {file} carefully. Focus on {concern}.",
  "category": "review",
  "tags": ["review", "risk"],
  "language": "en",
  "created_at": "2026-06-29T00:00:00Z",
  "updated_at": "2026-06-29T00:00:00Z"
}
```

Before every add, edit, or delete, the previous database is copied to:

```text
~/.always/sentences.backup.json
```

This is a single rolling backup, not a version history.

## Repository Layout

```text
Always/
├── README.md
├── README.zh.md
├── PROJECT_DETAILS.md
├── 项目详解.md
├── LICENSE
├── assets/
│   ├── architecture-light.svg
│   └── architecture-dark.svg
├── scripts/
│   └── install.sh
└── skills/always/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── assets/sentences.sample.json
    └── scripts/always.py
```

## Verification

From the repository root:

```bash
python3 -m py_compile skills/always/scripts/always.py
bash -n scripts/install.sh
python3 skills/always/scripts/always.py --help
```

For an isolated data smoke test, set `HOME` to a temporary directory before running `seed`, `add`, `edit`, and `delete`. Do not use `seed --force` against your real home unless you intend to reset the live library.

## Privacy & Safety

- Saved sentences are plain-text JSON on your machine. Do not store secrets, tokens, passwords, or private keys.
- Native paste targets the frontmost application. Keep focus on the intended input before selecting a sentence.
- The backup is stored beside the primary database on the same disk; it is not disaster recovery.
- There is no multi-process write lock. Avoid running simultaneous add/edit/delete operations.
- `seed --force` replaces the live database with sample content after writing the rolling backup.
- Moving the source checkout breaks the installed symlinks until `scripts/install.sh` is run again from the new location.

## Requirements

| Dependency | Needed for | Notes |
|---|---|---|
| Python 3.10+ | All CLI operations | Standard library only. |
| macOS | Native picker and automatic paste | Uses AppleScript, `pbcopy`, and System Events. |
| Bash | Installer | Preinstalled on macOS and most Linux systems. |
| Accessibility permission | Automatic `Cmd+V` | Not needed for print-only CLI usage. |

## Design Details

For the mechanism, capability boundary, tradeoffs, risks, and maintainer map, read [PROJECT_DETAILS.md](PROJECT_DETAILS.md). Chinese version: [项目详解.md](项目详解.md).

## Contributing

Issues and pull requests are welcome. Useful contributions include tests, additional platform adapters, stronger schema validation, safer concurrent writes, and picker usability improvements. Keep the core promise intact: local, inspectable, editable, and user-controlled.

## License

[MIT](LICENSE) © 2026 yc星辰

---

<div align="center">

*Write the instruction once. Keep it available everywhere you work with an agent.*

</div>
