#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

BUILD_DIR="build/lambda_package"
ZIP_FILE="build/lambda_package.zip"

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

echo "Building ingestion Lambdas for Python 3.12"

command -v podman >/dev/null 2>&1 || fail "Podman is required."
command -v zip >/dev/null 2>&1 || fail "zip is required."

[[ -f src/ingestion/eirgrid_ingestion.py ]] || fail "EirGrid source missing."
[[ -f src/ingestion/openmeteo_ingestion.py ]] || fail "Open-Meteo source missing."

rm -rf "$BUILD_DIR" "$ZIP_FILE"
mkdir -p "$BUILD_DIR"

echo "Copying complete application source..."
cp -a src "$BUILD_DIR/"

cat > "$BUILD_DIR/requirements.txt" <<'EOF'
requests==2.31.0
urllib3==2.0.7
loguru==0.7.2
pandas==2.2.2
numpy==1.26.4
pyarrow==16.1.0
EOF

echo "Installing Python 3.12 dependencies..."
podman run --rm \
    --entrypoint /bin/bash \
    -v "$PROJECT_ROOT/$BUILD_DIR:/workspace:Z" \
    public.ecr.aws/lambda/python:3.12 \
    -c "cd /workspace && pip install --no-cache-dir -r requirements.txt -t . && pip check"

rm -f "$BUILD_DIR/requirements.txt"

echo "Cleaning Python cache..."
find "$BUILD_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "$BUILD_DIR" -type f -name "*.pyc" -delete

echo "Creating ZIP..."
(
    cd "$BUILD_DIR"
    zip -qr "../lambda_package.zip" .
)

echo "Verifying package structure..."
python3 - "$ZIP_FILE" <<'PY'
import sys
import zipfile

required = [
    "src/__init__.py",
    "src/ingestion/eirgrid_ingestion.py",
    "src/ingestion/openmeteo_ingestion.py",
    "src/common/config.py",
    "src/monitoring/service.py",
    "src/observability/models.py",
    "src/observability/collector.py",
    "src/observability/metrics.py",
    "src/quality/models.py",
]

with zipfile.ZipFile(sys.argv[1]) as archive:
    names = set(archive.namelist())
    missing = [name for name in required if name not in names]
    if missing:
        raise SystemExit(f"Missing required files: {missing}")
    print(f"Verified {len(required)} required files.")
    print(f"Total ZIP entries: {len(names)}")
PY

echo "Testing Lambda imports in Python 3.12..."
podman run --rm \
    --entrypoint /var/lang/bin/python \
    -v "$PROJECT_ROOT/$BUILD_DIR:/workspace:ro,Z" \
    -e PYTHONPATH=/workspace \
    public.ecr.aws/lambda/python:3.12 \
    -c '
import sys, requests, urllib3, loguru, boto3
from src.ingestion.eirgrid_ingestion import lambda_handler as eirgrid_handler
from src.ingestion.openmeteo_ingestion import lambda_handler as openmeteo_handler
from src.monitoring.service import MonitoringService
from src.observability.collector import ObservabilityCollector

print("Python:", sys.version)
print("Requests:", requests.__version__)
print("urllib3:", urllib3.__version__)
print("Loguru:", loguru.__version__)
print("Boto3:", boto3.__version__)
print("EirGrid:", eirgrid_handler.__name__)
print("Open-Meteo:", openmeteo_handler.__name__)
print("MonitoringService:", MonitoringService.__name__)
print("ObservabilityCollector:", ObservabilityCollector.__name__)
print("SUCCESS: ingestion imports passed")
'

echo
echo "SUCCESS: Ingestion package built."
echo "Archive: $ZIP_FILE"
ls -lh "$ZIP_FILE"
