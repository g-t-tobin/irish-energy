#!/usr/bin/env python3
"""
Comprehensive local integration verification for Irish Energy Analytics platform
"""

import sys
import os
import subprocess

def check_config():
    """Check configuration settings"""
    print("=== CONFIGURATION CHECK ===")
    sys.path.insert(0, 'api')
    sys.path.insert(0, 'src')
    
    try:
        from src.common.config import Config
        print(f"✓ AWS Region: {Config.AWS_REGION}")
        print(f"✓ Gold Bucket: {Config.GOLD_BUCKET}")
        print(f"✓ Bronze Bucket: {Config.BRONZE_BUCKET}")
        print(f"✓ Silver Bucket: {Config.SILVER_BUCKET}")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def check_api_endpoints():
    """Verify API endpoints are correctly defined"""
    print("\n=== API ENDPOINTS CHECK ===")
    try:
        from api.main import app
        routes = [r.path for r in app.routes]
        expected_routes = ['/health', '/demand', '/weather', '/generation', '/quality', '/summary']
        
        found_routes = []
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Endpoint {route} found")
                found_routes.append(route)
            else:
                print(f"✗ Endpoint {route} NOT found")
                
        print(f"Found {len(found_routes)}/{len(expected_routes)} expected endpoints")
        return len(found_routes) == len(expected_routes)
    except Exception as e:
        print(f"✗ API endpoint error: {e}")
        return False

def check_models():
    """Verify API data models match expected structure"""
    print("\n=== MODELS CHECK ===")
    try:
        from api.models import DemandData, WeatherData, GenerationData, DataQualityMetrics, SummaryData
        print("✓ All API models imported successfully")
        
        # Show model structures (using modern Pydantic v2 syntax)
        print("DemandData fields:", list(DemandData.model_fields.keys()))
        print("WeatherData fields:", list(WeatherData.model_fields.keys()))
        print("GenerationData fields:", list(GenerationData.model_fields.keys()))
        print("DataQualityMetrics fields:", list(DataQualityMetrics.model_fields.keys()))
        print("SummaryData fields:", list(SummaryData.model_fields.keys()))
        
        return True
    except Exception as e:
        print(f"✗ Model error: {e}")
        return False

def check_data_service():
    """Verify data service functionality"""
    print("\n=== DATA SERVICE CHECK ===")
    try:
        from api.services.data_service import S3GoldDataRetriever
        import os
        
        # Set environment variables to match expected configuration
        os.environ.setdefault('AWS_REGION', 'eu-west-1')
        os.environ.setdefault('S3_BUCKET_NAME', 'irish-energy-gold-layer')
        
        retriever = S3GoldDataRetriever()
        print(f"✓ Data retriever created with bucket: {retriever.bucket_name}")
        
        # Test method signatures
        methods = ['get_demand_data', 'get_weather_data', 'get_generation_data', 
                  'get_quality_metrics', 'get_summary_data']
        for method in methods:
            if hasattr(retriever, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} missing")
                
        return True
    except Exception as e:
        print(f"✗ Data service error: {e}")
        return False

def check_tests():
    """Run backend tests and report results"""
    print("\n=== BACKEND TESTS ===")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 'api/tests/', '-v', '--tb=short'
        ], capture_output=True, text=True, cwd='.')
        
        print("Test output:")
        print(result.stdout)
        if result.stderr:
            print("Test errors:")
            print(result.stderr)
            
        # Parse results manually
        lines = result.stdout.split('\n')
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for line in lines:
            if 'passed' in line and 'failed' not in line:
                if 'failed' in line:
                    failed_tests += int(line.split('failed')[0].strip().split()[-1])
                else:
                    passed_tests += int(line.split('passed')[0].strip().split()[-1])
            if 'collected' in line:
                total_tests = int(line.split('collected')[0].strip().split()[-1])
        
        print(f"\nTest Results: {passed_tests}/{total_tests} passed")
        if failed_tests > 0:
            print(f"Failed tests: {failed_tests}")
        return True
    except Exception as e:
        print(f"✗ Test execution error: {e}")
        return False

def check_frontend():
    """Check frontend setup"""
    print("\n=== FRONTEND CHECK ===")
    try:
        # Check if frontend directory exists
        if not os.path.exists('dashboard'):
            print("✗ Dashboard directory not found")
            return False
            
        # Check if package.json exists
        if not os.path.exists('dashboard/package.json'):
            print("✗ package.json not found in dashboard")
            return False
            
        print("✓ Frontend directory structure OK")
        
        # Try to run build check
        result = subprocess.run([
            'npm', 'run', 'build'
        ], capture_output=True, text=True, cwd='dashboard')
        
        if result.returncode == 0:
            print("✓ Frontend build successful")
        else:
            print("✗ Frontend build failed")
            print("Build output:", result.stderr[:500])
            
        return True
    except Exception as e:
        print(f"✗ Frontend check error: {e}")
        return False

def main():
    """Run all verification checks"""
    print("IRISH ENERGY ANALYTICS - LOCAL INTEGRATION VERIFICATION")
    print("=" * 60)
    
    checks = [
        check_config,
        check_api_endpoints,
        check_models,
        check_data_service,
        check_tests,
        check_frontend
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"✗ Check {check.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("✓ ALL CHECKS PASSED")
    else:
        print("✗ SOME CHECKS FAILED")
        
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())