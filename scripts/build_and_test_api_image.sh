#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${API_IMAGE:-irish-energy-api-lambda:local}"
CONTEXT="$ROOT/build/api_container_context"
REGION="${AWS_REGION:-eu-west-1}"
GOLD_BUCKET="${GOLD_BUCKET:-irish-energy-gold-851725545966-eu-west-1}"

if command -v podman >/dev/null 2>&1; then
  ENGINE=podman
elif command -v docker >/dev/null 2>&1; then
  ENGINE=docker
else
  echo "ERROR: Podman or Docker is required for a Lambda container image build." >&2
  exit 1
fi

"$ROOT/scripts/prepare_api_image_context.sh"

printf '\n==> Building %s with %s (linux/amd64)\n' "$IMAGE" "$ENGINE"
"$ENGINE" build --platform linux/amd64 -f "$CONTEXT/Dockerfile" -t "$IMAGE" "$CONTEXT"

printf '\n==> Testing Lambda handler and FastAPI app in read-only container\n'
"$ENGINE" run --rm --platform linux/amd64 \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=512m \
  --entrypoint /bin/bash \
  -e AWS_LAMBDA_FUNCTION_NAME=irish-energy-api-container-smoke-test \
  -e AWS_REGION="$REGION" \
  -e AWS_DEFAULT_REGION="$REGION" \
  -e AWS_EC2_METADATA_DISABLED=true \
  -e STORAGE_BACKEND=s3 \
  -e GOLD_BUCKET="$GOLD_BUCKET" \
  "$IMAGE" -lc 'cd "$LAMBDA_TASK_ROOT" && python - <<"PY"
from lambda_handler import handler
from main import app

assert callable(handler), "Lambda handler is not callable"
assert app.title == "Irish Energy Analytics API", app.title
print("PASS: Lambda handler imported")
print(f"PASS: FastAPI application imported: {app.title}")
print("PASS: application imports in read-only Lambda container")
PY'

printf '\n==> Image build and isolated import test passed\n'
"$ENGINE" image inspect "$IMAGE" --format 'Image ID: {{.Id}} | Architecture: {{.Architecture}}'
