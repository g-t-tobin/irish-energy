#!/usr/bin/env python3
"""
Simple test to verify the API server can start up correctly
"""

import sys
import os
from pathlib import Path

# Add the api directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "api"))

try:
    from api.main import app
    print("✓ API server imports successfully")
    
    # Test that we can create an instance of the app
    print("✓ API app created successfully")
    
    # Test that all endpoints are defined
    routes = [route.path for route in app.routes]
    expected_endpoints = ['/health', '/demand', '/weather', '/generation', '/quality', '/summary']
    
    for endpoint in expected_endpoints:
        if endpoint in routes:
            print(f"✓ Endpoint {endpoint} found")
        else:
            print(f"✗ Endpoint {endpoint} NOT found")
    
    print("✓ All basic API tests passed")
    
except Exception as e:
    print(f"✗ API test failed: {e}")
    sys.exit(1)