#!/usr/bin/env bash
set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BUILD_DIR="build/lambda_package"
ZIP_FILE="build/lambda_package.zip"

fail() {
    echo -e "${RED}ERROR: $*${NC}" >&2
    exit 1
}

echo -e "${GREEN}Building ingestion Lambdas for Python 3.12${NC}"

command -v podman >/dev/null 2>&1 || fail "Podman is required."
command -v zip >/dev/null 2>&1 || fail "zip is required."
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required."

[[ -f "src/ingestion/eirgrid_ingestion.py" ]] ||
    fail "EirGrid ingestion source not found."

[[ -f "src/ingestion/openmeteo_ingestion.py" ]] ||
    fail "OpenMeteo ingestion source not found."

rm -rf "${BUILD_DIR}" "${ZIP_FILE}"

mkdir -p "${BUILD_DIR}/src/ingestion"
mkdir -p "${BUILD_DIR}/src/common"

echo -e "${YELLOW}Copying ingestion source files...${NC}"

cp src/__init__.py "${BUILD_DIR}/src/"
cp src/ingestion/__init__.py "${BUILD_DIR}/src/ingestion/"
cp src/ingestion/eirgrid_ingestion.py "${BUILD_DIR}/src/ingestion/"
cp src/ingestion/openmeteo_ingestion.py "${BUILD_DIR}/src/ingestion/"
cp src/common/__init__.py "${BUILD_DIR}/src/common/"
cp src/common/config.py "${BUILD_DIR}/src/common/"

echo -e "${YELLOW}Creating pinned requirements...${NC}"

cat > "${BUILD_DIR}/requirements.txt" <<'EOF'
requests==2.31.0
urllib3==2.0.7
loguru==0.7.2
EOF

echo -e "${YELLOW}Installing dependencies in Python 3.12...${NC}"

podman run --rm \
    --entrypoint /bin/bash \
    -v "$(pwd)/${BUILD_DIR}:/workspace:Z" \
    public.ecr.aws/lambda/python:3.12 \
    -c "cd /workspace && pip install --no-cache-dir -r requirements.txt -t . && pip check"

rm -f "${BUILD_DIR}/requirements.txt"

echo -e "${YELLOW}Cleaning cache files...${NC}"

find "${BUILD_DIR}" -type d -name "__pycache__" \
    -prune -exec rm -rf {} +

find "${BUILD_DIR}" -type f -name "*.pyc" -delete

echo -e "${YELLOW}Creating ZIP archive...${NC}"

(
    cd "${BUILD_DIR}"
    zip -qr "../lambda_package.zip" .
)

echo -e "${YELLOW}Verifying package structure...${NC}"

python3 - "${ZIP_FILE}" <<'PY'
import sys
import zipfile

required = [
    "src/__init__.py",
    "src/ingestion/__init__.py",
    "src/ingestion/eirgrid_ingestion.py",
    "src/ingestion/openmeteo_ingestion.py",
    "src/common/__init__.py",
    "src/common/config.py",
    "requests/__init__.py",
    "urllib3/__init__.py",
    "loguru/__init__.py",
]

with zipfile.ZipFile(sys.argv[1]) as archive:
    names = set(archive.namelist())
    missing = [name for name in required if name not in names]

    if missing:
        raise SystemExit(f"Missing required files: {missing}")

    print(f"Verified {len(required)} required files.")
    print(f"Total ZIP entries: {len(names)}")

print("SUCCESS: Ingestion ZIP structure verified.")
PY

echo -e "${YELLOW}Testing both ingestion Lambda imports in Python 3.12...${NC}"

podman run --rm \
    --entrypoint /var/lang/bin/python \
    -v "$(pwd)/${BUILD_DIR}:/workspace:ro,Z" \
    -e PYTHONPATH=/workspace \
    public.ecr.aws/lambda/python:3.12 \
    -c '
import sys
import requests
import urllib3
import loguru
import boto3

from src.ingestion.eirgrid_ingestion import lambda_handler as eirgrid_handler
from src.ingestion.openmeteo_ingestion import lambda_handler as openmeteo_handler
from src.common.config import Config

print("Python:", sys.version)
print("Requests:", requests.__version__)
print("urllib3:", urllib3.__version__)
print("Loguru:", loguru.__version__)
print("Boto3:", boto3.__version__)
print("EirGrid handler:", eirgrid_handler.__name__)
print("OpenMeteo handler:", openmeteo_handler.__name__)
print("SUCCESS: All ingestion imports passed")
'

echo
echo -e "${GREEN}Ingestion package built successfully.${NC}"
echo "Archive: ${ZIP_FILE}"
ls -lh "${ZIP_FILE}"
