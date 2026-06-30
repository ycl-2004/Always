#!/usr/bin/env python3
"""Manage and paste reusable personal sentences for the always skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Formatter


APP_DIR = Path.home() / ".always"
DB_PATH = APP_DIR / "sentences.json"
BACKUP_PATH = APP_DIR / "sentences.backup.json"
SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = SCRIPT_DIR.parent / "assets" / "sentences.sample.json"


class AlwaysError(Exception):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_sample() -> dict:
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


def ensure_db() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text(json.dumps(load_sample(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_db() -> dict:
    ensure_db()
    try:
        data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AlwaysError(f"Invalid JSON in {DB_PATH}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("sentences"), list):
        raise AlwaysError(f"{DB_PATH} must contain an object with a sentences list")
    return data


def write_db(data: dict) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, BACKUP_PATH)
    tmp = DB_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(DB_PATH)


def normalize_id(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def sentence_id(sentence: dict) -> str:
    return str(sentence.get("id", "")).strip()


def all_sentences(data: dict) -> list[dict]:
    return data.get("sentences", [])


def find_by_id(data: dict, item_id: str) -> dict | None:
    for sentence in all_sentences(data):
        if sentence_id(sentence) == item_id:
            return sentence
    return None


def searchable_text(sentence: dict) -> str:
    fields = [
        sentence.get("id", ""),
        sentence.get("title", ""),
        sentence.get("text", ""),
        sentence.get("category", ""),
        sentence.get("language", ""),
        " ".join(str(tag) for tag in sentence.get("tags", [])),
    ]
    return "\n".join(str(field).lower() for field in fields)


def search_sentences(data: dict, query: str | None) -> list[dict]:
    sentences = all_sentences(data)
    if not query:
        return sentences
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return sentences
    results = []
    for sentence in sentences:
        haystack = searchable_text(sentence)
        if all(term in haystack for term in terms):
            results.append(sentence)
    return results


def preview(text: str, width: int = 90) -> str:
    text = " ".join(text.split())
    if len(text) <= width:
        return text
    return text[: width - 1].rstrip() + "…"


def print_sentences(sentences: list[dict]) -> None:
    if not sentences:
        print("No matching sentences.")
        return
    current_category = None
    for index, sentence in enumerate(sentences, 1):
        category = str(sentence.get("category", "uncategorized"))
        if category != current_category:
            if current_category is not None:
                print()
            print(f"[{category}]")
            current_category = category
        title = sentence.get("title") or sentence_id(sentence)
        print(f"{index}. {sentence_id(sentence)} — {title}")
        print(f"   {preview(str(sentence.get('text', '')))}")


def extract_variables(template: str) -> list[str]:
    variables = []
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name and field_name not in variables:
            variables.append(field_name)
    return variables


def parse_var(values: list[str] | None) -> dict[str, str]:
    parsed = {}
    for item in values or []:
        if "=" not in item:
            raise AlwaysError(f"Variable must use name=value format: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise AlwaysError(f"Variable name cannot be empty: {item}")
        parsed[key] = value
    return parsed


def render_text(template: str, values: dict[str, str], prompt_missing: bool, prompter=None) -> str:
    missing = [name for name in extract_variables(template) if name not in values]
    for name in missing:
        if not prompt_missing:
            raise AlwaysError(f"Missing variable: {name}")
        values[name] = prompter(name) if prompter else input(f"{name}: ")
    try:
        return template.format(**values)
    except KeyError as exc:
        raise AlwaysError(f"Missing variable: {exc.args[0]}") from exc


def choose_sentence(sentences: list[dict], choice: int | None) -> dict:
    if not sentences:
        raise AlwaysError("No matching sentences.")
    if choice is None:
        print_sentences(sentences)
        raw = input("Choose a number: ").strip()
        if not raw.isdigit():
            raise AlwaysError("Choice must be a number.")
        choice = int(raw)
    if choice < 1 or choice > len(sentences):
        raise AlwaysError(f"Choice must be between 1 and {len(sentences)}.")
    return sentences[choice - 1]


def copy_to_clipboard(text: str) -> None:
    process = subprocess.run(["pbcopy"], input=text, text=True, capture_output=True)
    if process.returncode != 0:
        raise AlwaysError(process.stderr.strip() or "pbcopy failed")


def applescript_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def run_applescript(script: str) -> tuple[int, str, str]:
    process = subprocess.run(["osascript", "-e", script], text=True, capture_output=True)
    return process.returncode, process.stdout.strip(), process.stderr.strip()


def paste_into_frontmost() -> tuple[bool, str]:
    script = '''
delay 0.2
tell application "System Events"
  keystroke "v" using command down
end tell
'''
    code, out, err = run_applescript(script)
    if code == 0:
        return True, ""
    return False, err or out or "osascript failed"


def native_menu(sentences: list[dict], title: str = "Always") -> dict | None:
    if not sentences:
        raise AlwaysError("No matching sentences.")
    labels = []
    for index, sentence in enumerate(sentences, 1):
        label = sentence.get("title") or sentence_id(sentence)
        labels.append(f"{index}. {label}")
    items = ", ".join(applescript_quote(label) for label in labels)
    script = f'''
set theList to {{{items}}}
set theChoice to choose from list theList with title {applescript_quote(title)} with prompt "Pick a sentence:" OK button name "Use" cancel button name "Cancel"
if theChoice is false then
  return "__CANCELLED__"
else
  return item 1 of theChoice
end if
'''
    code, out, err = run_applescript(script)
    if code != 0:
        raise AlwaysError(err or out or "osascript failed")
    if not out or out == "__CANCELLED__":
        return None
    number = out.split(".", 1)[0].strip()
    if not number.isdigit():
        raise AlwaysError(f"Unexpected menu selection: {out}")
    return sentences[int(number) - 1]


def native_prompt(name: str) -> str:
    script = f'''
set theResponse to display dialog {applescript_quote(name + ":")} with title "Always" default answer "" buttons {{"Cancel", "OK"}} default button "OK"
return text returned of theResponse
'''
    code, out, _err = run_applescript(script)
    if code != 0:
        raise AlwaysError("Cancelled.")
    return out


def output_text(text: str, paste: bool) -> None:
    if not paste:
        print(text)
        return
    copy_to_clipboard(text)
    ok, message = paste_into_frontmost()
    if ok:
        print("Pasted into the frontmost app without pressing Enter.")
    else:
        print("Copied to clipboard, but paste automation failed.")
        print(message)
        print()
        print(text)


def prompt(default: str | None, label: str, required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""


def prompt_tags(default: list[str] | None = None) -> list[str]:
    default_text = ", ".join(default or [])
    raw = prompt(default_text, "Tags comma-separated")
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def build_sentence(args: argparse.Namespace, existing: dict | None = None, new_id: str | None = None) -> dict:
    base = existing or {}
    title = args.title or prompt(base.get("title"), "Title", required=True)
    item_id = new_id or getattr(args, "id", None) or base.get("id") or normalize_id(title)
    item_id = normalize_id(item_id)
    if not item_id:
        raise AlwaysError("ID cannot be empty.")
    text = args.text or prompt(base.get("text"), "Text", required=True)
    category = args.category or prompt(base.get("category", "general"), "Category", required=True)
    language = args.language or prompt(base.get("language", "mixed"), "Language", required=True)
    tags = args.tag if args.tag is not None else prompt_tags(base.get("tags", []))
    created_at = base.get("created_at") or now_iso()
    return {
        "id": item_id,
        "title": title,
        "text": text,
        "category": category,
        "tags": tags,
        "language": language,
        "created_at": created_at,
        "updated_at": now_iso(),
    }


def cmd_seed(args: argparse.Namespace) -> int:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists() and not args.force:
        print(f"Database already exists: {DB_PATH}")
        return 0
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, BACKUP_PATH)
    DB_PATH.write_text(json.dumps(load_sample(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Seeded {DB_PATH}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    data = load_db()
    print_sentences(search_sentences(data, args.query))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    data = load_db()
    print_sentences(search_sentences(data, args.query))
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    data = load_db()
    sentence = find_by_id(data, args.id)
    if sentence is None:
        raise AlwaysError(f"Unknown sentence id: {args.id}")
    text = render_text(str(sentence.get("text", "")), parse_var(args.var), prompt_missing=args.prompt_missing)
    output_text(text, args.paste)
    return 0


def cmd_pick(args: argparse.Namespace) -> int:
    data = load_db()
    matches = search_sentences(data, args.query)
    sentence = choose_sentence(matches, args.choice)
    text = render_text(str(sentence.get("text", "")), parse_var(args.var), prompt_missing=args.prompt_missing)
    output_text(text, args.paste)
    return 0


def cmd_menu(args: argparse.Namespace) -> int:
    data = load_db()
    matches = search_sentences(data, args.query)
    sentence = native_menu(matches)
    if sentence is None:
        print("Cancelled.")
        return 0
    text = render_text(
        str(sentence.get("text", "")),
        parse_var(args.var),
        prompt_missing=True,
        prompter=native_prompt,
    )
    output_text(text, args.paste)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    data = load_db()
    sentence = build_sentence(args)
    if find_by_id(data, sentence["id"]) is not None:
        raise AlwaysError(f"Duplicate sentence id: {sentence['id']}")
    data["sentences"].append(sentence)
    write_db(data)
    print(f"Added {sentence['id']}")
    return 0


def cmd_edit(args: argparse.Namespace) -> int:
    data = load_db()
    existing = find_by_id(data, args.id)
    if existing is None:
        raise AlwaysError(f"Unknown sentence id: {args.id}")
    updated = build_sentence(args, existing, new_id=args.new_id)
    if updated["id"] != args.id and find_by_id(data, updated["id"]) is not None:
        raise AlwaysError(f"Duplicate sentence id: {updated['id']}")
    sentences = all_sentences(data)
    for index, sentence in enumerate(sentences):
        if sentence_id(sentence) == args.id:
            sentences[index] = updated
            break
    write_db(data)
    print(f"Updated {updated['id']}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    data = load_db()
    existing = find_by_id(data, args.id)
    if existing is None:
        raise AlwaysError(f"Unknown sentence id: {args.id}")
    if not args.force:
        answer = input(f"Delete {args.id}? Type yes to confirm: ").strip().lower()
        if answer != "yes":
            print("Delete cancelled.")
            return 0
    data["sentences"] = [s for s in all_sentences(data) if sentence_id(s) != args.id]
    write_db(data)
    print(f"Deleted {args.id}")
    return 0


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--var", action="append", help="Variable value in name=value format. May be repeated.")
    parser.add_argument("--no-prompt-missing", dest="prompt_missing", action="store_false", help="Fail instead of prompting for missing variables.")
    parser.set_defaults(prompt_missing=True)
    parser.add_argument("--paste", action="store_true", help="Copy to clipboard and paste into macOS Terminal without pressing Enter.")


def add_edit_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--id", help="Sentence id. Defaults to a slug from the title.")
    parser.add_argument("--title", help="Short display title.")
    parser.add_argument("--text", help="Sentence text.")
    parser.add_argument("--category", help="Category name.")
    parser.add_argument("--language", help="Language code or label.")
    parser.add_argument("--tag", action="append", help="Tag. May be repeated.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage reusable personal sentences.")
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="Create or reset the database from sample data.")
    seed.add_argument("--force", action="store_true", help="Overwrite existing database after writing the single backup.")
    seed.set_defaults(func=cmd_seed)

    list_parser = sub.add_parser("list", help="List saved sentences.")
    list_parser.add_argument("query", nargs="?", help="Optional contains search.")
    list_parser.set_defaults(func=cmd_list)

    search = sub.add_parser("search", help="Search saved sentences.")
    search.add_argument("query", nargs="?", default="", help="Search query.")
    search.set_defaults(func=cmd_search)

    get = sub.add_parser("get", help="Print or paste a sentence by id.")
    get.add_argument("id", help="Sentence id.")
    add_common_options(get)
    get.set_defaults(func=cmd_get)

    pick = sub.add_parser("pick", help="Search, choose, then print or paste a sentence.")
    pick.add_argument("query", nargs="?", default="", help="Search query.")
    pick.add_argument("--choice", type=int, help="1-based choice number.")
    add_common_options(pick)
    pick.set_defaults(func=cmd_pick)

    menu = sub.add_parser("menu", help="Pop a native macOS picker, then paste the chosen sentence.")
    menu.add_argument("query", nargs="?", default="", help="Optional filter applied before the picker opens.")
    menu.add_argument("--var", action="append", help="Variable value in name=value format. May be repeated.")
    menu.add_argument("--no-paste", dest="paste", action="store_false", help="Print the sentence instead of pasting it.")
    menu.set_defaults(func=cmd_menu, paste=True, prompt_missing=True)

    add = sub.add_parser("add", help="Add a sentence interactively or with flags.")
    add_edit_options(add)
    add.set_defaults(func=cmd_add)

    edit = sub.add_parser("edit", help="Edit a sentence interactively or with flags.")
    edit.add_argument("id", help="Existing sentence id.")
    edit.add_argument("--new-id", help="New sentence id. Defaults to the existing id.")
    edit.add_argument("--title", help="Short display title.")
    edit.add_argument("--text", help="Sentence text.")
    edit.add_argument("--category", help="Category name.")
    edit.add_argument("--language", help="Language code or label.")
    edit.add_argument("--tag", action="append", help="Tag. May be repeated.")
    edit.set_defaults(func=cmd_edit)

    delete = sub.add_parser("delete", help="Delete a sentence.")
    delete.add_argument("id", help="Sentence id.")
    delete.add_argument("--force", action="store_true", help="Delete without confirmation.")
    delete.set_defaults(func=cmd_delete)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except AlwaysError as exc:
        print(f"always: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
