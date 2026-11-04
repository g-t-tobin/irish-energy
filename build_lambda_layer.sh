#!/bin/bash

# Build a slim AWS Lambda Python 3.12 layer containing:
# pandas, numpy and pyarrow.
#
# The resulting archive has python/ at its root, as Lambda requires.

set -Eeuo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

LAYER_DIR="build/pandas_pyarrow_layer"
LAYER_ZIP="build/pandas_pyarrow_layer.zip"
TRANSFORMATION_ZIP="build/transformation_package.zip"
LAMBDA_LIMIT=262144000

fail() {
    echo -e "${RED}ERROR: $*${NC}" >&2
    exit 1
}

if ! command -v podman >/dev/null 2>&1; then
    fail "Podman is required."
fi

if [[ ! -d "layers/pandas_pyarrow_layer" ]]; then
    fail "Run this script from the project root."
fi

if [[ ! -f "${TRANSFORMATION_ZIP}" ]]; then
    fail "Transformation package not found: ${TRANSFORMATION_ZIP}"
fi

echo -e "${GREEN}Building Lambda layer using Python 3.12...${NC}"

rm -rf "${LAYER_DIR}" "${LAYER_ZIP}"
mkdir -p "${LAYER_DIR}/python"

# Install dependencies in the Lambda Python 3.12 environment.
podman run --rm \
    --entrypoint /bin/bash \
    -v "$(pwd)/layers/pandas_pyarrow_layer:/workspace:ro,Z" \
    -v "$(pwd)/${LAYER_DIR}:/output:Z" \
    public.ecr.aws/lambda/python:3.12 \
    -c 'pip install --no-cache-dir \
        -r /workspace/requirements.txt \
        -t /output/python'

PYARROW_DIR="${LAYER_DIR}/python/pyarrow"

[[ -d "${PYARROW_DIR}" ]] || fail "PyArrow installation not found."

echo -e "${YELLOW}Removing unused PyArrow components...${NC}"

# These optional components are not used by the application.
rm -f "${PYARROW_DIR}"/_flight*.so
rm -f "${PYARROW_DIR}"/libarrow_flight.so*
rm -f "${PYARROW_DIR}"/libarrow_python_flight.so

rm -f "${PYARROW_DIR}"/_substrait*.so
rm -f "${PYARROW_DIR}"/libarrow_substrait.so*

echo -e "${YELLOW}Removing development files and caches...${NC}"

rm -rf "${PYARROW_DIR}/tests"
rm -rf "${PYARROW_DIR}/include"
rm -rf "${PYARROW_DIR}/src"

find "${LAYER_DIR}/python" \
    -type d -name '__pycache__' -prune -exec rm -rf {} +

find "${LAYER_DIR}/python" \
    -type f -name '*.pyc' -delete

echo -e "${YELLOW}Creating Lambda layer archive...${NC}"

# IMPORTANT: python/ must be at the archive root.
(
    cd "${LAYER_DIR}"
    zip -qr "../pandas_pyarrow_layer.zip" python
)

echo -e "${YELLOW}Checking ZIP structure...${NC}"

python3 - "${LAYER_ZIP}" <<'ZIPCHECK'
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1]) as archive:
    names = archive.namelist()

if not names or names[0] != "python/":
    raise SystemExit("ERROR: python/ is not at the ZIP root")

print("SUCCESS: python/ is at the ZIP root")
ZIPCHECK

echo -e "${YELLOW}Testing imports and Parquet functionality...${NC}"

podman run --rm \
    --entrypoint /bin/bash \
    -v "$(pwd)/${LAYER_DIR}:/workspace:ro,Z" \
    public.ecr.aws/lambda/python:3.12 \
    -c 'PYTHONPATH=/workspace/python python - <<'"'"'PY'"'"'
import io
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

print("Pandas:", pd.__version__)
print("NumPy:", np.__version__)
print("PyArrow:", pa.__version__)

original = pd.DataFrame({
    "date": pd.date_range("2026-01-01", periods=3),
    "demand": [4200.5, 4350.2, 4100.8],
    "region": ["Ireland", "Ireland", "Ireland"]
})

table = pa.Table.from_pandas(original)

buffer = io.BytesIO()
pq.write_table(table, buffer)

buffer.seek(0)
restored = pq.read_table(buffer).to_pandas()

pd.testing.assert_frame_equal(original, restored)

print("SUCCESS: Parquet round-trip passed")
PY'

echo -e "${YELLOW}Checking combined uncompressed Lambda size...${NC}"

python3 - "${LAYER_ZIP}" "${TRANSFORMATION_ZIP}" "${LAMBDA_LIMIT}" <<'PY'
import sys
import zipfile

layer_path, function_path, limit = sys.argv[1:]
limit = int(limit)

def uncompressed_size(path):
    with zipfile.ZipFile(path) as archive:
        return sum(item.file_size for item in archive.infolist())

layer_size = uncompressed_size(layer_path)
function_size = uncompressed_size(function_path)
total = layer_size + function_size

print(f"Layer:         {layer_size:,} bytes")
print(f"Function:      {function_size:,} bytes")
print(f"Combined:      {total:,} bytes")
print(f"Lambda limit:  {limit:,} bytes")
print(f"Headroom:      {limit - total:,} bytes")

if total > limit:
    raise SystemExit("ERROR: Combined deployment exceeds Lambda limit.")

print("SUCCESS: Combined deployment is within Lambda's size limit.")
PY

echo -e "${GREEN}Lambda layer build completed successfully.${NC}"
echo "Archive: ${LAYER_ZIP}"
ls -lh "${LAYER_ZIP}"
