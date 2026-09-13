#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This launcher is for macOS. On Thor use ./run-coinscope.sh"
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required: https://brew.sh"
  exit 1
fi

brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg

PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
if [[ ! -d .venv-mac ]]; then
  "$PYTHON" -m venv .venv-mac
fi
.venv-mac/bin/python -m pip install --upgrade pip
.venv-mac/bin/pip install -r requirements.txt opencv-python

if ! curl -fsS --max-time 2 http://127.0.0.1:8081/v1/models >/dev/null 2>&1; then
  echo "Connecting securely to Gemma Vision on Thor..."
  ssh -fN \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -L 8081:127.0.0.1:8081 \
    mnahtygal@y-thor.local
fi

if ! curl -fsS --max-time 3 http://127.0.0.1:8081/v1/models >/dev/null 2>&1; then
  echo "Gemma Vision is not reachable through Thor."
  echo "Confirm Thor is on and its llama-server is running on port 8081."
  exit 1
fi

echo "Starting CoinScope at http://127.0.0.1:5050"
(sleep 2; open http://127.0.0.1:5050) &
exec .venv-mac/bin/python app.py
