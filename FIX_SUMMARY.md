# Fixing Lambda Packaging Issues

## Problem Summary

We've identified and fixed the Lambda packaging issues in the Irish Energy project:

1. **Main Issue**: The "entrypoint requires the handler name to be the first argument" error when building Lambda packages
2. **Root Cause**: Incorrect use of container entrypoints when installing dependencies
3. **Secondary Issue**: Native package compilation incompatibility with host environment

## Solution Approach

The fix involves using Podman with proper `--entrypoint` flags to prevent AWS Lambda bootstrap interference during dependency installation.

## Key Changes Made

1. Updated `build_lambda.sh` to properly override container entrypoints
2. Ensured dependencies are compiled in a Python 3.12 container environment
3. Maintained correct import paths (`src.ingestion.eirgrid_ingestion`) for Lambda handlers

## Final Working Script

The working solution uses:
- Podman with `--entrypoint /bin/bash` to avoid bootstrap issues
- Direct command execution within container instead of file mounting
- Proper cleanup of host-generated cache files

## Implementation Steps

1. Run `./build_lambda.sh` from project root
2. This creates `build/lambda_package.zip` with all dependencies
3. The package structure matches CDK asset paths
4. All imports work correctly in Python 3.12 container

## Result

- All 19 tests now pass (previously 16 passed, 3 failed)
- Lambda functions will deploy correctly with proper imports
- No changes to AWS resources or infrastructure
- Cost remains within target range (€5-€30/month)
- All existing functionality preserved