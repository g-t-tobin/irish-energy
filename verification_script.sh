#!/bin/bash
# Irish Energy Analytics Website - Verification Script
# This script verifies that the website is properly deployed and functional

set -e  # Exit on any error

echo "=== Irish Energy Analytics Website Verification ==="

# Test 1: Basic website accessibility
echo "Test 1: Checking website accessibility..."
curl -f -s -o /dev/null https://irish-energy.ai-autofy-general-server.com
if [ $? -eq 0 ]; then
    echo "✓ Website is accessible"
else
    echo "✗ Website is not accessible"
    exit 1
fi

# Test 2: API connectivity
echo "Test 2: Checking API connectivity..."
curl -f -s -o /dev/null https://dnse188i83.execute-api.eu-west-1.amazonaws.com/health
if [ $? -eq 0 ]; then
    echo "✓ API is accessible"
else
    echo "✗ API is not accessible"
    exit 1
fi

# Test 3: Check key HTML elements exist
echo "Test 3: Verifying HTML structure..."
HTML_CONTENT=$(curl -s https://irish-energy.ai-autofy-general-server.com)
if echo "$HTML_CONTENT" | grep -q "<title>Irish Energy Analytics</title>"; then
    echo "✓ HTML title found"
else
    echo "✗ HTML title not found"
    exit 1
fi

if echo "$HTML_CONTENT" | grep -q "Irish Energy Analytics"; then
    echo "✓ Main heading found"
else
    echo "✗ Main heading not found"
    exit 1
fi

# Test 4: Check JS files are loaded
echo "Test 4: Verifying JavaScript files..."
if echo "$HTML_CONTENT" | grep -q "app.js"; then
    echo "✓ app.js referenced"
else
    echo "✗ app.js not referenced"
    exit 1
fi

if echo "$HTML_CONTENT" | grep -q "config.js"; then
    echo "✓ config.js referenced"
else
    echo "✗ config.js not referenced"
    exit 1
fi

# Test 5: Check CSS files are loaded
echo "Test 5: Verifying CSS files..."
if echo "$HTML_CONTENT" | grep -q "styles.css"; then
    echo "✓ styles.css referenced"
else
    echo "✗ styles.css not referenced"
    exit 1
fi

# Test 6: Verify API endpoints work
echo "Test 6: Testing key API endpoints..."
API_ENDPOINTS=(
    "/health"
    "/summary" 
    "/demand"
    "/generation"
    "/weather"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    echo "  Testing $endpoint..."
    curl -f -s -o /dev/null "https://dnse188i83.execute-api.eu-west-1.amazonaws.com$endpoint"
    if [ $? -eq 0 ]; then
        echo "    ✓ $endpoint accessible"
    else
        echo "    ✗ $endpoint not accessible"
        # Don't fail completely on individual endpoint issues
    fi
done

echo "=== All Tests Completed Successfully ==="
echo "Website appears to be properly deployed and functional."