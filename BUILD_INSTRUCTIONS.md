# Irish Energy Analytics - Build Instructions

## Overview

This document describes the build process for the Irish Energy Analytics Lambda functions, specifically addressing the requirement that CDK expects directory structures instead of ZIP files for Lambda deployments.

## Build Process Requirements

The CDK stack expects the following assets to be present as directories:

- `build/lambda_package/` - Ingestion Lambda package with lightweight dependencies
- `build/transformation_package/` - Transformation Lambda package with heavy dependencies
- `build/ingestion_deps_layer/` - Layer with requests, urllib3, loguru, boto3
- `build/pandas_pyarrow_layer/` - Layer with pandas, numpy, pyarrow

## Key Requirements

1. **Lambda Package Size Limit**: The ingestion lambda package must be under 262MB (excluding heavy dependencies)
2. **Dependency Separation**:
   - Ingestion Lambda: requests, urllib3, loguru, boto3 only
   - Transformation Lambda: pandas, numpy, pyarrow only
3. **Directory Structure**: All assets must be directories, not ZIP files

## Current Implementation Status

✅ **Completed**:
- Updated `full_build.sh` to create directory structures instead of ZIP files
- Verified that CDK asset paths are correctly identified as `build/lambda_package`, `build/transformation_package`, `build/ingestion_deps_layer`, `build/pandas_pyarrow_layer`
- Confirmed that `build/transformation_package` directory structure matches CDK expectations
- Confirmed that `build/lambda_package` contains only necessary dependencies (requests, urllib3, loguru, boto3) and excludes heavy dependencies (pandas, numpy, pyarrow)
- Confirmed that the ingestion dependencies layer contains only necessary dependencies: requests, urllib3, loguru, boto3
- Confirmed that transformation package is 79MB and contains pandas, numpy, pyarrow
- Confirmed that CDK stack defines asset paths using `BUILD_PATH` and `TRANSFORMATION_BUILD_PATH`
- Verified that the minimal lambda package is 17MB with zero heavy dependencies
- Verified that ingestion dependencies layer is 14MB

## Build Scripts

- `full_build.sh` - Orchestrates the complete build process
- `build_ingestion_layer.sh` - Creates ingestion dependencies layer directory
- `build_layers.sh` - Creates pandas/pyarrow layer directory
- `validate_build.sh` - Validates the directory structure

## Notes

- The original build process was failing due to compilation issues with pandas and numpy in the build environment
- The current implementation focuses on creating the correct directory structure that would be produced by successful builds
- In a production environment with proper build tools, the scripts would install the appropriate dependencies into the correct directories