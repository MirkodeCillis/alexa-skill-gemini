#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

echo "==> Step 1: Remove stale lambda/alexa_gemini/"
rm -rf "$ROOT/lambda/alexa_gemini"

echo "==> Step 2: Copy src/alexa_gemini -> lambda/alexa_gemini/"
cp -r "$ROOT/src/alexa_gemini" "$ROOT/lambda/alexa_gemini"

echo "==> Step 3: Install pinned deps into lambda/"
pip install -r "$ROOT/lambda/requirements.txt" --target "$ROOT/lambda" --quiet

echo "==> Done. lambda/ is ready for upload to the Alexa Developer Console."
