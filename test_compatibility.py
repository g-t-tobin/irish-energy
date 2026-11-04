#!/usr/bin/env python3
"""
Test script to verify the API compatibility fix works correctly
"""

import sys
import os
sys.path.insert(0, 'api')

from api.models.frontend_compatibility import (
    FrontendDemandData, FrontendWeatherData, FrontendGenerationData,
    FrontendDataQualityMetrics, FrontendSummaryData,
    convert_api_to_frontend_demand, convert_api_to_frontend_weather,
    convert_api_to_frontend_generation, convert_api_to_frontend_quality,
    convert_api_to_frontend_summary
)
from api.models import DemandData, WeatherData, GenerationData, DataQualityMetrics, SummaryData

def test_conversion_functions():
    print("Testing API to Frontend Conversion Functions...")
    
    # Test Demand conversion
    print("\n1. Testing Demand Conversion:")
    api_demand = [
        DemandData(
            timestamp="2023-01-01T00:00:00",
            demand_mw=100.0,
            demand_mwh=50.0,
            forecast_mw=90.0,
            forecast_mwh=45.0
        )
    ]
    
    frontend_demand = convert_api_to_frontend_demand(api_demand)
    print(f"Input: {api_demand[0]}")
    print(f"Output: {frontend_demand[0]}")
    assert isinstance(frontend_demand[0], FrontendDemandData)
    print("✓ Demand conversion works")
    
    # Test Weather conversion
    print("\n2. Testing Weather Conversion:")
    api_weather = [
        WeatherData(
            timestamp="2023-01-01T00:00:00",
            temperature_celsius=15.0,
            humidity_percent=60.0,
            wind_speed_mps=5.0,
            wind_direction_degrees=180.0,
            pressure_hpa=1013.0,
            precipitation_mm=0.0
        )
    ]
    
    frontend_weather = convert_api_to_frontend_weather(api_weather)
    print(f"Input: {api_weather[0]}")
    print(f"Output: {frontend_weather[0]}")
    assert isinstance(frontend_weather[0], FrontendWeatherData)
    print("✓ Weather conversion works")
    
    # Test Generation conversion
    print("\n3. Testing Generation Conversion:")
    api_generation = [
        GenerationData(
            timestamp="2023-01-01T00:00:00",
            renewable_generation_mw=60.0,
            fossil_generation_mw=40.0,
            nuclear_generation_mw=20.0,
            total_generation_mw=120.0
        )
    ]
    
    frontend_generation = convert_api_to_frontend_generation(api_generation)
    print(f"Input: {api_generation[0]}")
    print(f"Output: {frontend_generation[0]}")
    assert isinstance(frontend_generation[0], FrontendGenerationData)
    print("✓ Generation conversion works")
    
    # Test Quality conversion
    print("\n4. Testing Quality Conversion:")
    api_quality = [
        DataQualityMetrics(
            dataset_name="test_dataset",
            total_records=1000,
            missing_values=10,
            data_quality_score=0.95,
            last_updated="2023-01-01T00:00:00"
        )
    ]
    
    frontend_quality = convert_api_to_frontend_quality(api_quality)
    print(f"Input: {api_quality[0]}")
    print(f"Output: {frontend_quality[0]}")
    assert isinstance(frontend_quality[0], FrontendDataQualityMetrics)
    print("✓ Quality conversion works")
    
    # Test Summary conversion
    print("\n5. Testing Summary Conversion:")
    api_summary = SummaryData(
        total_datasets=5,
        total_records=10000,
        last_updated="2023-01-01T00:00:00",
        data_quality_summary={"overall_score": 0.95}
    )
    
    frontend_summary = convert_api_to_frontend_summary(api_summary)
    print(f"Input: {api_summary}")
    print(f"Output: {frontend_summary}")
    assert isinstance(frontend_summary, FrontendSummaryData)
    print("✓ Summary conversion works")
    
    print("\n🎉 All conversion functions work correctly!")

if __name__ == "__main__":
    test_conversion_functions()