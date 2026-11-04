#!/usr/bin/env bash
set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BUILD_DIR="build/transformation_package"
ZIP_FILE="build/transformation_package.zip"

fail() {
    echo -e "${RED}ERROR: $*${NC}" >&2
    exit 1
}

echo -e "${GREEN}Building transformation Lambda for Python 3.12${NC}"

command -v podman >/dev/null 2>&1 || fail "Podman is required."
command -v zip >/dev/null 2>&1 || fail "zip is required."
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required."

[[ -f "src/transformation/handler.py" ]] ||
    fail "Run this script from the project root."

[[ -f "src/transformation/data_transformation.py" ]] ||
    fail "DataTransformer source not found."

rm -rf "${BUILD_DIR}" "${ZIP_FILE}"

mkdir -p "${BUILD_DIR}/transformation"
mkdir -p "${BUILD_DIR}/src/transformation"
mkdir -p "${BUILD_DIR}/src/common"

echo -e "${YELLOW}Copying transformation source files...${NC}"

cp src/transformation/handler.py "${BUILD_DIR}/transformation/"
cp src/transformation/data_transformation.py "${BUILD_DIR}/src/transformation/"
cp src/transformation/quality_checks.py "${BUILD_DIR}/src/transformation/"
cp src/transformation/bronze_layer.py "${BUILD_DIR}/src/transformation/"
cp src/transformation/silver_layer.py "${BUILD_DIR}/src/transformation/"
cp src/transformation/gold_layer.py "${BUILD_DIR}/src/transformation/"
cp src/common/config.py "${BUILD_DIR}/src/common/"

touch "${BUILD_DIR}/transformation/__init__.py"
touch "${BUILD_DIR}/src/__init__.py"
touch "${BUILD_DIR}/src/transformation/__init__.py"
touch "${BUILD_DIR}/src/common/__init__.py"

echo "loguru==0.7.2" > "${BUILD_DIR}/requirements.txt"

echo -e "${YELLOW}Installing Loguru in Python 3.12 container...${NC}"

podman run --rm \
    --entrypoint /bin/bash \
    -v "$(pwd)/${BUILD_DIR}:/workspace:Z" \
    public.ecr.aws/lambda/python:3.12 \
    -c "cd /workspace && pip install --no-cache-dir -r requirements.txt -t ."

rm -f "${BUILD_DIR}/requirements.txt"

find "${BUILD_DIR}" -type d -name "__pycache__" \
    -prune -exec rm -rf {} +
find "${BUILD_DIR}" -type f -name "*.pyc" -delete

echo -e "${YELLOW}Creating transformation ZIP...${NC}"

(
    cd "${BUILD_DIR}"
    zip -qr "../transformation_package.zip" .
)

echo -e "${YELLOW}Verifying ZIP structure...${NC}"

python3 - "${ZIP_FILE}" <<'PY'
import sys
import zipfile

required = [
    "transformation/handler.py",
    "src/__init__.py",
    "src/transformation/__init__.py",
    "src/transformation/data_transformation.py",
    "src/transformation/quality_checks.py",
    "src/transformation/bronze_layer.py",
    "src/transformation/silver_layer.py",
    "src/transformation/gold_layer.py",
    "src/common/__init__.py",
    "src/common/config.py",
    "loguru/__init__.py",
]

with zipfile.ZipFile(sys.argv[1]) as archive:
    names = set(archive.namelist())
    missing = [name for name in required if name not in names]

    if missing:
        raise SystemExit(f"Missing required files: {missing}")

    print(f"Verified {len(required)} required files.")
    print(f"Total ZIP entries: {len(names)}")

print("SUCCESS: Transformation ZIP structure verified.")
PY

echo -e "${GREEN}Transformation package created: ${ZIP_FILE}${NC}"
