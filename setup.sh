#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$ROOT_DIR"

mkdir -p .mplconfig .cache plots data/faces OUTPUT

python3 -m pip install -r requirements.txt

echo
echo "Setup completed."
echo "Run the app with:"
echo "python3 main.py"
