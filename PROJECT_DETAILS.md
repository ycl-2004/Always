# Always Project Details

[English](PROJECT_DETAILS.md) | [中文](项目详解.md) | [Back to README](README.md)

> This document explains the mechanism, capability boundary, tradeoffs, risks, and maintainer workflow. User-facing installation and commands live in the README.

## 1. For a First-Time Reader: What It Is & Why Use It

Always is a local reusable prompt/snippet system for AI-agent conversations and fast desktop entry. It stores reusable instructions once and exposes the same library through Raycast, Codex, Claude Code, and the CLI.

**The problem it solves**: useful instructions are repetitive. Users repeatedly ask an agent to plan first, preserve behavior, review a file for a specific risk, answer in a preferred tone, or verify before completion. Rewriting those instructions costs time and leads to wording drift.

**The core promise**:

```text
save once -> find quickly -> fill variables -> paste -> review -> send
```

**Why this shape**:

- Personal instructions should stay inspectable and editable.
- Raycast, Codex, and Claude Code should use the same source instead of separate snippet stores.
- Selection should be faster than searching a notes app or waiting for an agent round trip.
- Pasting should never silently submit an instruction.
- The tool should not require a service, API key, database server, or Python package installation.

**What it is not**:

- It is not project memory or a task handoff log. Use ShareMemory for project-scoped cross-agent state.
- It is not a document manager; entries are text instructions, not attachments.
- It is not a secrets vault; data is plain-text JSON.
- It is not a prompt marketplace or synchronization service.
- It is not a full clipboard manager.

## 2. How It Actually Works

The installed system has four parts:

```text
Always source checkout
  scripts/install.sh
  scripts/raycast/
    always.sh                 Raycast launcher for the native picker
    open-json.sh              Raycast launcher for the live JSON file
    _always_common.zsh        shared Raycast script helpers
  skills/always/
    SKILL.md                  agent behavior and routing
    scripts/always.py        CLI, picker, rendering, persistence
    assets/sentences.sample.json

Raycast entry
  Add <repo>/scripts/raycast as a Script Directory
  Bind Always to a global hotkey, usually double Option (⌥⌥)

Agent discovery
  ~/.agents/skills/always    -> source checkout (Codex)
  ~/.claude/skills/always    -> source checkout (Claude Code)

Personal runtime data
  ~/.always/sentences.json
  ~/.always/sentences.backup.json
```

### 2.1 Installation model

`scripts/install.sh` creates symlinks, not copies. Both agents therefore execute the same `SKILL.md` and `always.py`. Updating the source checkout updates both agent integrations immediately.

The installer creates the database from the bundled sample only when `~/.always/sentences.json` is missing. Reinstalling does not reset personal content.

Raycast integration is intentionally explicit rather than automatic: the user adds `<repo>/scripts/raycast` as a Raycast Script Directory and assigns a hotkey in Raycast Settings. The installer prints the directory path but does not modify Raycast preferences.

### 2.2 Selection model

The core picker is `always.py menu`. The skill defaults to it because it removes a conversational round trip, and Raycast makes it reachable without opening an agent conversation at all:

1. Load the JSON database.
2. Apply optional query terms.
3. Present matching titles through AppleScript.
4. Resolve `{variables}` through native dialogs.
5. Copy the rendered text with `pbcopy`.
6. Send `Cmd+V` to the frontmost app.
7. Stop without pressing Enter.

When GUI automation is unavailable, `list`, `search`, `get`, and `pick` provide a text-only path.

### 2.3 Raycast model

Raycast commands are thin launchers:

- `scripts/raycast/always.sh` locates Python and the repository-relative `always.py`, then runs `menu`.
- `scripts/raycast/open-json.sh` opens `~/.always/sentences.json` in the user's default editor, seeding the database first if it does not exist.
- `_always_common.zsh` centralizes path and Python discovery so command files do not hard-code `/opt/homebrew/bin/python3` or a specific checkout path.

Raycast does not own persistence, search, rendering, backup, or paste behavior. Those stay in the core Python CLI so Codex, Claude Code, direct CLI use, and Raycast do not diverge.

### 2.4 Search model

Search concatenates these fields:

```text
id + title + text + category + language + tags
```

It lowercases both the query and searchable content. Every whitespace-separated query term must be a substring of the combined content. There is no tokenization, fuzzy matching, scoring, stemming, or language-specific segmentation.

### 2.5 Write model

Add, edit, and delete load the full JSON object, modify the in-memory `sentences` list, then:

1. Copy the current database to `sentences.backup.json`.
2. Write formatted UTF-8 JSON to `sentences.json.tmp`.
3. Atomically replace the primary database with the temporary file.

The temporary replace protects against partial primary-file writes. The rolling backup protects only the immediately previous state.

### 2.6 Variable model

Variables use `string.Formatter` syntax such as `{file}`. Values come from repeated `--var name=value` arguments or interactive prompts. Rendering occurs at selection time; the stored template is unchanged. The special `{files}` variable is list-valued: the native `menu` flow opens a macOS multi-file picker, text prompts split newline-separated, comma-separated, or shell-escaped values, and repeated `--var files=...` CLI arguments render as an inline list.

## 3. Capability Boundary

### What it can do reliably

- Share one local personal instruction library between Raycast, Codex, Claude Code, and direct CLI use.
- Launch the same picker from a Raycast global hotkey.
- Open the live JSON database from Raycast for direct inspection or editing.
- List and search multilingual content.
- Select through a native macOS dialog.
- Render reusable templates with named variables.
- Paste without automatic submission.
- Add, edit, rename, and delete entries by ID.
- Preserve one pre-write backup.
- Initialize a missing database from sample content.
- Operate without third-party Python dependencies.

### What it cannot currently do

- Synchronize content between machines.
- Coordinate simultaneous writers.
- Encrypt saved content.
- Provide full history or per-entry rollback.
- Fuzzy-search or rank results by relevance or usage frequency.
- Attach files, images, or rich documents.
- Guarantee paste goes to the intended app if focus changes.
- Provide a native GUI editor for the sentence library.
- Validate every field against a strict JSON schema.
- Offer first-class non-macOS picker and paste adapters.
- Configure Raycast automatically; the user must add the Script Directory and hotkey manually.

## 4. Personal Snippets vs Project Memory

Always and ShareMemory solve different context problems:

| Dimension | Always | ShareMemory |
|---|---|---|
| Scope | One person's reusable instructions | One project's shared agent state |
| Storage | `~/.always/sentences.json` | `<project>/AI_MEMORY/` |
| Typical content | Tone, review prompts, workflow commands | Decisions, tasks, learnings, handoffs |
| Lifetime | Cross-project and long-lived | Bound to a repository |
| Invocation | Pick or search a sentence | Read/update project memory protocol |
| Git suitability | Usually private and outside repositories | Optionally reviewed with the project |

Do not put project decisions into Always: they will be detached from the project and can become stale. Do not put personal cross-project preferences into ShareMemory: they add noise to project handoffs.

## 5. Short-Term vs Long-Term Use

| Dimension | Small library | Large, long-lived library |
|---|---|---|
| Selection | Fast visual scan | Menu becomes harder to scan |
| Search | Simple filters are sufficient | Lack of fuzzy ranking becomes visible |
| Categories | Lightweight organization | No enforced taxonomy; naming can drift |
| Backup | One generation is usually enough | Accidental older changes cannot be recovered |
| Portability | One local file is convenient | Cross-machine sync must be handled separately |
| Maintenance | Almost none | Duplicate and stale prompts require manual cleanup |

The current implementation is strongest for a curated personal library of concise, high-value instructions. It is not optimized for thousands of snippets or long-form document storage.

## 6. Project-Wise Pros and Cons

### Advantages

- **Plain JSON**: easy to inspect, back up, diff, and migrate.
- **One shared source**: Raycast, Codex, and Claude Code do not drift into separate prompt libraries.
- **Raycast-first speed**: a global hotkey opens the same picker without an agent round trip.
- **Fast native path**: one command and one click for the common case.
- **User-controlled send**: automatic paste never means automatic execution.
- **No service dependency**: no account, network, API key, or hosted database.
- **Parameterized reuse**: `{variables}` turn one sentence into a family of instructions.
- **Small implementation**: one Python script and one shell installer are easy to audit.

### Disadvantages

- **macOS-centric UX**: the best experience depends on AppleScript and System Events.
- **Single rolling backup**: not enough for deep recovery.
- **No concurrent-write protocol**: last writer wins, and the fixed temporary path can conflict.
- **Basic search**: no fuzzy matching, ranking, aliases, or usage statistics.
- **Loose validation**: malformed entry fields can survive if the top-level structure is valid.
- **Source checkout coupling**: moving or deleting the source checkout breaks the agent symlinks and the Raycast Script Directory until they are repointed.
- **Plain-text privacy model**: safe only for content the user is comfortable storing locally in clear text.

## 7. Complete Risk List

### Data and persistence

1. **One-generation recovery**: each write overwrites the previous backup, so only the immediately preceding database can be restored.
2. **Same-disk backup**: the primary and backup fail together if the home directory or disk is lost.
3. **Concurrent writes**: there is no lock. Two processes can read the same old state and overwrite each other's changes.
4. **Shared temporary filename**: simultaneous writes target the same `.json.tmp` path.
5. **Partial schema validation**: the loader checks for an object with a `sentences` list but does not validate every entry or field type.
6. **Manual JSON edits**: direct edits bypass rolling backup behavior and can make the entire database invalid JSON.
7. **Destructive reset**: `seed --force` intentionally replaces the live library after one backup.

### Selection and rendering

8. **Focus-sensitive paste**: a user can change focus between selection and `Cmd+V`, sending text to the wrong application.
9. **Accessibility dependency**: System Events paste fails when the launching app lacks permission.
10. **Clipboard exposure**: selected text remains in the system clipboard until replaced.
11. **Template syntax errors**: unmatched braces or unsupported formatting expressions can fail at render time.
12. **Title-only native menu**: categories and previews are not visible in the picker, so duplicate or vague titles reduce usability.
13. **Basic AND search**: a broad or differently worded query may return nothing even when a conceptually related sentence exists.

### Identity and organization

14. **ASCII ID normalization**: automatic IDs remove non-ASCII characters; all-Chinese titles need an explicit ID.
15. **No taxonomy enforcement**: category and tag spelling can drift (`writing`, `write`, `写作`).
16. **Rename references**: changing an ID can break aliases, scripts, or documentation that used the old ID.
17. **Tag replacement semantics**: passing `--tag` during edit replaces the full tag list rather than merging it.

### Installation and distribution

18. **Moved source checkout**: absolute symlink targets and the Raycast Script Directory become invalid after the repository moves.
19. **Existing directory conflict**: the installer refuses to replace non-symlink paths, which is safe but requires manual resolution.
20. **Platform asymmetry**: installation and text CLI functions can work beyond macOS, but `menu` and `--paste` are macOS-specific.
21. **No current automated test suite**: verification depends on syntax checks and smoke tests until tests and CI are added.
22. **Future data migrations**: the file contains `version: 1`, but no migration framework exists yet.
23. **Raycast PATH differences**: Raycast may not inherit an interactive shell PATH, so its scripts must resolve Python defensively.
24. **Raycast setting drift**: renamed scripts, moved directories, or changed hotkeys can leave user documentation out of sync with local Raycast preferences.

### Privacy

25. **Plain-text storage**: anyone with access to the user account can read the saved prompts.
26. **Accidental secret capture**: users may save credentials inside a convenient reusable sentence even though Always is not a vault.
27. **Screen and history exposure**: printed sentences can appear in terminal scrollback, screenshots, shell automation logs, or agent transcripts.

## 8. Who It Fits

**Strong fit**:

- macOS users who want a Raycast global hotkey for reusable prompts.
- People who use Codex and/or Claude Code and want the same library available inside agent conversations.
- Users with a curated set of recurring prompts and operating preferences.
- macOS users who value a one-click native picker.
- Users who prefer transparent local files over a hosted snippet service.
- Solo workflows where write operations are sequential.

**Use cautiously or choose another tool**:

- Teams needing shared, permissioned, remotely synchronized snippets.
- Users storing secrets or regulated data.
- Large libraries requiring fuzzy search, ranking, analytics, or rich editing.
- Concurrent automation that may write from multiple processes.
- Non-macOS users who require the full native picker experience.

## 9. Maintainer Catch-Up (5 Minutes)

Read and verify in this order:

1. `git status --short` and `git diff --stat` after the repository is initialized with git.
2. `skills/always/SKILL.md` for agent-facing behavior and workflow rules.
3. `scripts/raycast/` for Raycast launcher behavior and hotkey setup docs.
4. `skills/always/scripts/always.py` for CLI, persistence, search, rendering, and paste behavior.
5. `skills/always/assets/sentences.sample.json` for first-run defaults.
6. `scripts/install.sh` for distribution paths and collision behavior.
7. `README.md` and `README.zh.md` for the public contract.
8. This bilingual details pair for design rationale and known risks.

| Question | Source of truth |
|---|---|
| Agent trigger and expected behavior | `skills/always/SKILL.md` |
| Raycast commands and setup | `scripts/raycast/README.md` + `scripts/raycast/*.sh` |
| CLI flags and runtime behavior | `skills/always/scripts/always.py` |
| Initial sample entries | `skills/always/assets/sentences.sample.json` |
| Install paths and linking | `scripts/install.sh` |
| Live user data | `~/.always/sentences.json` |
| Public usage contract | `README.md` + `README.zh.md` |
| Architecture, tradeoffs, and risks | `PROJECT_DETAILS.md` + `项目详解.md` |

Before a release candidate, run:

```bash
python3 -m py_compile skills/always/scripts/always.py
bash -n scripts/install.sh
zsh -n scripts/raycast/always.sh
zsh -n scripts/raycast/open-json.sh
python3 skills/always/scripts/always.py --help
```

Then run an isolated HOME smoke test covering `seed`, `list`, `search`, `get`, `add`, `edit`, and `delete`. Native picker and Raycast hotkey verification must be done interactively on macOS because they depend on focus, Raycast settings, and Accessibility state.

## Appendix A: Current Design Decisions

### A.1 One database outside the repository

Personal content belongs in `~/.always/`, not in the skill checkout. This separates code updates from user data and lets both agent integrations point to one library. The tradeoff is that git cloning the repository does not restore personal content.

### A.2 Symlink both agents to one skill copy

The installer links both discovery paths to `skills/always/`. This prevents code drift and makes updates immediate. Copy-based installs would be more portable after moving the source folder but would require explicit synchronization.

### A.2.1 Keep Raycast as a launcher, not the core

Raycast is the fastest user-facing entry point, but it should not own business logic. Script Commands stay thin and call the repository-local Python CLI. This keeps Raycast, Codex, Claude Code, and direct terminal use on one implementation and avoids duplicating search, rendering, backup, and paste behavior in shell scripts.

### A.3 Paste without Enter

Always treats a selected sentence as editable user input. It deliberately stops after paste so the user can review variables, context, and destination before execution.

### A.4 Rolling backup plus atomic replace

The current persistence model aims for a minimal safety floor without a database dependency: preserve the previous file, write a complete temporary JSON document, then replace the primary. It does not claim to provide concurrency safety or long-term history.

### A.5 Native picker as the default path

The picker minimizes agent conversation and visual scanning overhead for small libraries. Raycast makes that picker reachable globally; text-mode commands remain available for inspection, automation, and environments where GUI control is unavailable.

### A.6 Bilingual GitHub documentation baseline

The public documentation follows the same brand structure as ShareMemory: a centered bilingual entry, concise pain statement, honest capability boundary, paired English/Chinese details, and an MIT license under `yc星辰`. CI badges and test claims are intentionally omitted until the repository has real automation that supports them.
