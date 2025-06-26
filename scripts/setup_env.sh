#!/usr/bin/env bash
# scripts/setup_env.sh  ── quick dev-environment bootstrap
#
# Usage:
#   ./scripts/setup_env.sh        # creates .venv & installs requirements
#   source .venv/bin/activate     # activate the venv (remember each shell)
set -euo pipefail

# Determine which Python interpreter to use.
#
# Priority order:
#   1. Respect an explicit $PYTHON environment variable.
#   2. If a `python3.13` executable exists in PATH, use that (it is
#      typically installed alongside other minor versions and avoids any
#      ambiguity with an older default `python3`).
#   3. Fallback to the generic `python3` binary.

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="${PYTHON}"
else
  if command -v python3.13 &>/dev/null; then
    PYTHON_BIN="python3.13"
  else
    PYTHON_BIN="python3"
  fi
fi

VENV_DIR=".venv"

# Require Python ≥ 3.13
REQ_MAJOR=3
REQ_MINOR=13

# Helper: ensure a command exists
have() { command -v "$1" &>/dev/null; }

if ! have "$PYTHON_BIN"; then
  cat >&2 <<EOF
[setup] ❌  '$PYTHON_BIN' not found.

You need Python 3.13 or newer installed and discoverable in PATH.

Recommended installation methods:
  • macOS   :  brew install python@3.13
  • Ubuntu  :  sudo apt-get install python3.13 python3.13-venv
  • Fedora  :  sudo dnf install python3.13 python3.13-venv
  • Windows :  winget install --id Python.Python.3.13   (or use the official installer)

Alternatively use pyenv:
  curl https://pyenv.run | bash
  pyenv install 3.13.0 && pyenv local 3.13.0

Set the environment variable PYTHON to point at the 3.13 interpreter if it
is not named 'python3'.
EOF
  exit 1
fi

# Check interpreter version
CURRENT=$("$PYTHON_BIN" -V 2>&1 | awk '{print $2}')
MAJOR=${CURRENT%%.*}
MINOR=$(echo "$CURRENT" | cut -d. -f2)

if (( MAJOR < REQ_MAJOR || ( MAJOR == REQ_MAJOR && MINOR < REQ_MINOR ) )); then
  cat >&2 <<EOF
[setup] ❌  Python 3.13+ required, but '$PYTHON_BIN' is $CURRENT.

Use pyenv or your OS package manager to install a newer interpreter,
then re-run this script. See README for details.
EOF
  exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] Creating virtual environment in $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Activate
source "$VENV_DIR/bin/activate"

# Upgrade pip & install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "[setup] ✅  Environment ready."

python -m server.main
fastmcp run server/main.py 