#!/bin/bash

# Build Lambda layer for pandas and pyarrow
set -e

LAYER_DIR="layers/pandas_pyarrow_layer"
PYTHON_LIB_DIR="$LAYER_DIR/python"

# Clean previous build
rm -rf "$LAYER_DIR"
mkdir -p "$PYTHON_LIB_DIR"

# Install dependencies to layer directory
pip install --no-cache-dir -t "$PYTHON_LIB_DIR" pandas==2.1.3 pyarrow==15.0.0

# Create zip archive
cd "$LAYER_DIR"
zip -r "../pandas_pyarrow_layer.zip" .

echo "Layer built successfully: pandas_pyarrow_layer.zip"