#!/bin/bash

# Build script for API Lambda function with optimized dependencies
# This creates a lean deployment package that excludes unnecessary dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\0m' # No Color

echo -e "${GREEN}Starting API Lambda build process (optimized)${NC}"

# Remove previous build artifacts
rm -rf build/ api_lambda_package.zip
mkdir -p build/

# Create the lambda package directory with correct structure
echo -e "${YELLOW}Creating lambda package directory structure...${NC}"
mkdir -p build/api_lambda_package

# Copy all API source files to the package directory
echo -e "${YELLOW}Copying API source code...${NC}"
# Copy src directory to ensure all imports work correctly
if [ -d "src" ]; then
  echo -e "${YELLOW}Copying src directory...${NC}"
  cp -r src build/api_lambda_package/
else
  echo -e "${RED}Warning: src directory not found${NC}"
fi

cp -r api/* build/api_lambda_package/

# Remove any cached files that shouldn't be included
find build/api_lambda_package -name "*.pyc" -delete
find build/api_lambda_package -name "__pycache__" -type d -exec rm -rf {} +

# Create optimized requirements file for Lambda (excluding heavy dependencies that go in layer)
echo -e "${YELLOW}Creating optimized requirements file...${NC}"
cat > build/api_lambda_package/requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
mangum==0.17.0
loguru==0.7.2
EOF

# Install only the necessary dependencies in the build directory using Python 3.12 container
# This ensures compatibility with Lambda environment
echo -e "${YELLOW}Installing optimized dependencies in Python 3.12 container...${NC}"

# Try to use podman or docker
if command -v podman &> /dev/null; then
    CONTAINER_TOOL=podman
elif command -v docker &> /dev/null; then
    CONTAINER_TOOL=docker
else
    echo -e "${RED}Neither podman nor docker is available. Installing dependencies locally.${NC}"
    # Fall back to local installation
    pip install --no-cache-dir -r build/api_lambda_package/requirements.txt -t build/api_lambda_package
    echo -e "${GREEN}Dependencies installed locally${NC}"
    exit 0
fi

# Use container to install dependencies
$CONTAINER_TOOL run --rm \
  --entrypoint /bin/bash \
  -v "$(pwd)/build/api_lambda_package:/workspace:Z" \
  public.ecr.aws/lambda/python:3.12 \
  -c "
cd /workspace &&
pip install --no-cache-dir -r requirements.txt -t .
"

# Clean up any remaining cache files
echo -e "${YELLOW}Cleaning up cache files...${NC}"
find build/api_lambda_package -name "*.pyc" -delete
find build/api_lambda_package -name "__pycache__" -type d -exec rm -rf {} +

# Remove unnecessary files that contribute to bloat
echo -e "${YELLOW}Removing unnecessary files to reduce size...${NC}"
# Remove test directories and documentation
find build/api_lambda_package -name "tests" -type d -exec rm -rf {} +
find build/api_lambda_package -name "test*" -type d -exec rm -rf {} +
find build/api_lambda_package -name "*.md" -delete
find build/api_lambda_package -name "*.rst" -delete
find build/api_lambda_package -name "*.txt" -delete
find build/api_lambda_package -name "*.cfg" -delete
find build/api_lambda_package -name "*.toml" -delete
find build/api_lambda_package -name "*.pyc" -delete

# Remove large botocore data files that are not needed
echo -e "${YELLOW}Removing large botocore data files...${NC}"
find build/api_lambda_package -path "*/botocore/data/*" -name "*.json" -delete 2>/dev/null || true

# Remove Python cache files and __pycache__ directories
find build/api_lambda_package -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove large dependencies that aren't needed for the Lambda function
echo -e "${YELLOW}Removing large unnecessary dependencies...${NC}"
# Remove large timezone data files (tzdata) - we don't need all timezone info
find build/api_lambda_package -path "*/tzdata*" -type f -delete 2>/dev/null || true
# Remove pytz zoneinfo data (redundant with tzdata)
find build/api_lambda_package -path "*/pytz/zoneinfo*" -type f -delete 2>/dev/null || true

# Remove large documentation and license files
find build/api_lambda_package -name "LICENSE*" -delete 2>/dev/null || true
find build/api_lambda_package -name "README*" -delete 2>/dev/null || true
find build/api_lambda_package -name "AUTHORS*" -delete 2>/dev/null || true
find build/api_lambda_package -name "COPYING*" -delete 2>/dev/null || true
find build/api_lambda_package -name "THANKS*" -delete 2>/dev/null || true

# Remove large include directories that are not needed in Lambda
echo -e "${YELLOW}Removing large include directories...${NC}"
find build/api_lambda_package -path "*/include*" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove any heavy dependencies that might have snuck in (like pyarrow, pandas, numpy)
echo -e "${YELLOW}Removing heavy dependencies from API package...${NC}"
find build/api_lambda_package -path "*/pyarrow*" -type d -exec rm -rf {} + 2>/dev/null || true
find build/api_lambda_package -path "*/pandas*" -type d -exec rm -rf {} + 2>/dev/null || true
find build/api_lambda_package -path "*/numpy*" -type d -exec rm -rf {} + 2>/dev/null || true

# Create zip file
echo -e "${YELLOW}Creating zip package...${NC}"
cd build/api_lambda_package
zip -r ../api_lambda_package.zip ./*

echo -e "${GREEN}API Lambda package created successfully!${NC}"
echo -e "${YELLOW}Package size:${NC}"
du -h ../api_lambda_package.zip

# Verify the package structure
echo -e "${YELLOW}Verifying package structure...${NC}"
unzip -l ../api_lambda_package.zip | head -20

# Verify key dependencies are included
echo -e "${YELLOW}Checking for key dependencies in package:${NC}"
unzip -l ../api_lambda_package.zip | grep -E "(fastapi|mangum|pandas|pyarrow)" | head -10

# Test import in isolated environment
echo -e "${YELLOW}Testing import in isolated environment...${NC}"

# Create a test directory for isolated import test
mkdir -p test_isolated
cd test_isolated

# Extract the package to test directory
unzip ../api_lambda_package.zip

# Test imports in Python 3.12 container to verify compatibility
echo -e "${YELLOW}Testing imports in isolated Python 3.12 environment...${NC}"
if command -v podman &> /dev/null; then
    podman run --rm \
      -v "$(pwd):/workspace:ro,Z" \
      --entrypoint /bin/bash \
      public.ecr.aws/lambda/python:3.12 \
      -c "cd /workspace && PYTHONPATH=/workspace python -c \"from lambda_handler import handler; print('lambda_handler imported successfully'); from main import app; print('main app imported successfully'); import fastapi; import mangum; import pandas; import pyarrow; print('All dependencies imported successfully')\""
elif command -v docker &> /dev/null; then
    docker run --rm \
      -v "$(pwd):/workspace:ro,Z" \
      --entrypoint /bin/bash \
      public.ecr.aws/lambda/python:3.12 \
      -c "cd /workspace && PYTHONPATH=/workspace python -c \"from lambda_handler import handler; print('lambda_handler imported successfully'); from main import app; print('main app imported successfully'); import fastapi; import mangum; import pandas; import pyarrow; print('All dependencies imported successfully')\""
else
    # Fallback to local Python if containers not available
    python -c "from lambda_handler import handler; print('lambda_handler imported successfully'); from main import app; print('main app imported successfully'); import fastapi; import mangum; import pandas; import pyarrow; print('All dependencies imported successfully')"
fi

echo -e "${GREEN}Build and import test completed successfully!${NC}"