#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Always
# @raycast.mode silent

# Optional parameters:
# @raycast.icon ✍️
# @raycast.packageName Always
# @raycast.description Pick and paste a saved reusable instruction

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd -P)" || exit 1

source "${SCRIPT_DIR}/_always_common.zsh" || exit 1

PYTHON_BIN="$(always_python)" || exit 1
ALWAYS_SCRIPT="$(always_script_path "${SCRIPT_DIR}")" || exit 1

exec "${PYTHON_BIN}" "${ALWAYS_SCRIPT}" menu
