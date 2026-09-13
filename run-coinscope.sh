#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -c 'import cv2' >/dev/null 2>&1 || {
    echo "OpenCV is missing. Install it once with:"
    echo "  sudo apt update && sudo apt install -y python3-opencv python3-venv v4l-utils"
    exit 1
  }
  # Reuse Ubuntu/JetPack's camera-compatible OpenCV build.
  python3 -m venv --system-site-packages .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
fi
echo "Starting CoinScope at http://127.0.0.1:5050"
(sleep 2; xdg-open http://127.0.0.1:5050 >/dev/null 2>&1 || true) &
exec .venv/bin/python app.py
