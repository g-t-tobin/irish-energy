#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTEXT="$ROOT/build/api_container_context"

[[ -f "$ROOT/api/lambda_handler.py" ]] || { echo "ERROR: api/lambda_handler.py not found" >&2; exit 1; }
[[ -f "$ROOT/api/requirements.txt" ]] || { echo "ERROR: api/requirements.txt not found" >&2; exit 1; }
[[ -d "$ROOT/src" ]] || { echo "ERROR: src/ not found" >&2; exit 1; }

rm -rf "$CONTEXT"
mkdir -p "$CONTEXT"

# Copy the API package contents to Lambda's task root, matching the passing ZIP layout.
cp -a "$ROOT/api/." "$CONTEXT/"
cp -a "$ROOT/src" "$CONTEXT/src"
cp "$ROOT/Dockerfile.api" "$CONTEXT/Dockerfile"

# Keep build context lean and deterministic.
find "$CONTEXT" -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
find "$CONTEXT" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
rm -rf "$CONTEXT/tests" "$CONTEXT/api/tests" "$CONTEXT/.pytest_cache"
rm -f "$CONTEXT/models_backup.py" "$CONTEXT/models.py.bak"

printf 'Prepared API image context: %s\n' "$CONTEXT"
printf 'Context size: '
du -sh "$CONTEXT" | awk '{print $1}'
printf 'Handler: lambda_handler.handler\n'
printf 'Requirements: %s\n' "$CONTEXT/requirements.txt"
