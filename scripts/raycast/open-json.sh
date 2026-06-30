#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Always: Open JSON
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 📝
# @raycast.packageName Always
# @raycast.description Open the live Always sentence database

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd -P)" || exit 1

source "${SCRIPT_DIR}/_always_common.zsh" || exit 1

DB_PATH="$(always_database_path)"

if [[ ! -f "${DB_PATH}" ]]; then
  always_ensure_database "${SCRIPT_DIR}" || exit 1
fi

open "${DB_PATH}"
