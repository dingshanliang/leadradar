#!/usr/bin/env bash
# generate-types.sh - Generate TypeScript types from backend OpenAPI spec
#
# Usage:
#   ./scripts/generate-types.sh          # Export from Python module (no server needed)
#   ./scripts/generate-types.sh --live   # Fetch from running backend at localhost:8000
#
# Prerequisites:
#   - openapi-typescript installed (npm install -D openapi-typescript)
#   - For --live mode: backend running at localhost:8000
#   - For default mode: backend Python package installed in ../.venv

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WEB_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$WEB_DIR")"
OUTPUT_FILE="$WEB_DIR/src/lib/api-types.ts"
SPEC_FILE="$WEB_DIR/openapi.json"

cd "$WEB_DIR"

if [ "${1:-}" = "--live" ]; then
  # Fetch from running backend
  echo "Fetching OpenAPI spec from http://localhost:8000/openapi.json ..."
  if ! curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "ERROR: Backend is not running at http://localhost:8000"
    echo "Start it with: cd $PROJECT_ROOT && make dev"
    exit 1
  fi
  npx openapi-typescript http://localhost:8000/openapi.json -o "$OUTPUT_FILE"
else
  # Export from Python module (no server needed)
  VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
  if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Python venv not found at $VENV_PYTHON"
    echo "Create it with: cd $PROJECT_ROOT && make setup"
    exit 1
  fi

  echo "Exporting OpenAPI spec from Python module ..."
  "$VENV_PYTHON" -c "
from leadradar.main import app
import json
schema = app.openapi()
with open('$SPEC_FILE', 'w') as f:
    json.dump(schema, f, indent=2)
print('  -> $SPEC_FILE')
"

  echo "Generating TypeScript types ..."
  npx openapi-typescript "$SPEC_FILE" -o "$OUTPUT_FILE"
fi

echo ""
echo "Done! Types written to $OUTPUT_FILE"
echo "Review the generated types and update imports as needed."
