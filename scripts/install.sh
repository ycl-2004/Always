#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC="${ROOT}/skills/always"

if [[ ! -f "${SKILL_SRC}/SKILL.md" ]]; then
  echo "Cannot find ${SKILL_SRC}/SKILL.md" >&2
  exit 1
fi

mkdir -p "${HOME}/.agents/skills" "${HOME}/.claude/skills" "${HOME}/.always"

install_link() {
  local target="$1"
  if [[ -L "${target}" ]]; then
    rm "${target}"
  elif [[ -e "${target}" ]]; then
    echo "Refusing to replace existing non-symlink path: ${target}" >&2
    echo "Move it aside manually, then rerun this installer." >&2
    exit 1
  fi
  ln -s "${SKILL_SRC}" "${target}"
}

install_link "${HOME}/.agents/skills/always"
install_link "${HOME}/.claude/skills/always"

if [[ ! -f "${HOME}/.always/sentences.json" ]]; then
  cp "${SKILL_SRC}/assets/sentences.sample.json" "${HOME}/.always/sentences.json"
fi

echo "Installed always skill:"
echo "  Codex:      ${HOME}/.agents/skills/always"
echo "  Claude:     ${HOME}/.claude/skills/always"
echo "  Sentences:  ${HOME}/.always/sentences.json"
