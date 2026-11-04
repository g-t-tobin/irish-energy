#!/bin/bash

# Build script for Lambda functions using Python 3.12 containerized environment
# This script fixes the "entrypoint requires the handler name to be the first argument" error
# by properly overriding the container entrypoint when installing dependencies.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\0m' # No Color

# Check if podman is available
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Podman is required but not installed. Please install podman.${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
    echo -e "${RED}This script must be run from the project root directory${NC}"
    exit 1
fi

echo -e "${GREEN}Starting Lambda build process with Python 3.12 container${NC}"

# Create build directories
rm -rf build/ lambda_package.zip
mkdir -p build/

# Create the final lambda package directory with correct structure
echo -e "${YELLOW}Creating lambda package directory structure...${NC}"
mkdir -p build/lambda_package

# Copy source code to lambda package with proper directory structure
echo -e "${YELLOW}Copying source code...${NC}"
cp -r src build/lambda_package/

# Create requirements file in build directory to avoid permissions issues
echo -e "${YELLOW}Creating requirements file in build directory...${NC}"
cp requirements.txt build/lambda_package/requirements.txt

# Install dependencies directly using podman with inline command
echo -e "${YELLOW}Installing dependencies in Python 3.12 container...${NC}"

# Use a single command that avoids file mounting issues by copying requirements to build dir
podman run --rm \
  --entrypoint /bin/bash \
  -v "$(pwd)/build/lambda_package:/workspace:Z" \
  public.ecr.aws/lambda/python:3.12 \
  -c "
cd /workspace &&
pip install --no-cache-dir -r requirements.txt -t .
"

# Clean up any host-generated cache files
echo -e "${YELLOW}Removing host-generated cache files...${NC}"
find build/lambda_package -name "*.pyc" -delete
find build/lambda_package -name "__pycache__" -type d -exec rm -rf {} +

# Create zip file
echo -e "${YELLOW}Creating zip package...${NC}"
cd build/lambda_package
zip -r ../lambda_package.zip ./*

echo -e "${GREEN}Lambda package created successfully!${NC}"
echo -e "${YELLOW}Package size:${NC}"
du -h ../lambda_package.zip

# Verify the package structure
echo -e "${YELLOW}Verifying package structure...${NC}"
unzip -l ../lambda_package.zip | head -20

# Test import in Python 3.12 container to verify compatibility
echo -e "${YELLOW}Testing import compatibility...${NC}"
podman run --rm \
  -v "$(pwd)/../lambda_package:/workspace:ro,Z" \
  --entrypoint /bin/bash \
  public.ecr.aws/lambda/python:3.12 \
  -c "cd /workspace && PYTHONPATH=/workspace python -c \"import sys; print('Python version:', sys.version); import src.ingestion.eirgrid_ingestion; import src.ingestion.openmeteo_ingestion; import src.common.config; print('All imports successful')\""

echo -e "${GREEN}Build completed successfully!${NC}"