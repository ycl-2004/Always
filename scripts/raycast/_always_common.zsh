# Shared helpers for Always Raycast script commands.
#
# Keep this file non-executable and without Raycast metadata so Raycast treats it
# as an implementation detail, not as a command.

always_python() {
  if [[ -n "${ALWAYS_PYTHON:-}" ]]; then
    if [[ -x "${ALWAYS_PYTHON}" ]]; then
      if ! always_python_supported "${ALWAYS_PYTHON}"; then
        print -u2 -- "ALWAYS_PYTHON must point to Python 3.10 or newer: ${ALWAYS_PYTHON}"
        return 1
      fi
      print -r -- "${ALWAYS_PYTHON}"
      return 0
    fi
    print -u2 -- "ALWAYS_PYTHON is set but not executable: ${ALWAYS_PYTHON}"
    return 1
  fi

  local candidate resolved
  for candidate in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    resolved="$(command -v "${candidate}" 2>/dev/null || true)"
    if [[ -n "${resolved}" ]] && always_python_supported "${resolved}"; then
      print -r -- "${resolved}"
      return 0
    fi
    if [[ -x "${candidate}" ]] && always_python_supported "${candidate}"; then
      print -r -- "${candidate}"
      return 0
    fi
  done

  print -u2 -- "Could not find Python 3.10+. Install Python 3.10+ or set ALWAYS_PYTHON to an executable path."
  return 1
}

always_python_supported() {
  local python_bin="$1"
  "${python_bin}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

always_repo_root() {
  local script_dir="$1"
  local root
  root="$(cd -- "${script_dir}/../.." && pwd -P)" || return 1
  print -r -- "${root}"
}

always_script_path() {
  local script_dir="$1"
  local root script
  root="$(always_repo_root "${script_dir}")" || return 1
  script="${root}/skills/always/scripts/always.py"
  if [[ ! -f "${script}" ]]; then
    print -u2 -- "Always script not found: ${script}"
    return 1
  fi
  print -r -- "${script}"
}

always_database_path() {
  print -r -- "${HOME}/.always/sentences.json"
}

always_ensure_database() {
  local script_dir="$1"
  local python_bin always_script
  python_bin="$(always_python)" || return 1
  always_script="$(always_script_path "${script_dir}")" || return 1
  "${python_bin}" "${always_script}" seed >/dev/null
}
