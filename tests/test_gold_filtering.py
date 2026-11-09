"""
Test cases for Gold layer date filtering to reproduce the exact issue
"""
import pytest
import pandas as pd
from src.transformation.gold_layer import GoldLayerProcessor


def test_generation_filtering_with_cross_day_records():
    """Test that generation data properly filters out cross-day records"""

    # Create test data similar to the problematic 97-record dataset
    # Including the specific 7 November midnight record valued at 3118
    test_data = [
        # Records from the correct processing date (e.g., 2023-11-06)
        {'date': '2023-11-06', 'timestamp': '2023-11-06T00:00:00Z', 'value': 1000, 'fuel_type': 'wind'},
        {'date': '2023-11-06', 'timestamp': '2023-11-06T01:00:00Z', 'value': 1500, 'fuel_type': 'wind'},
        {'date': '2023-11-06', 'timestamp': '2023-11-06T23:00:00Z', 'value': 2000, 'fuel_type': 'wind'},

        # Cross-day record that should be excluded (midnight from next day)
        {'date': '2023-11-06', 'timestamp': '2023-11-07T00:00:00Z', 'value': 3118, 'fuel_type': 'solar'},

        # Another record from correct date
        {'date': '2023-11-06', 'timestamp': '2023-11-06T12:00:00Z', 'value': 2500, 'fuel_type': 'solar'},
    ]

    # Create DataFrame
    df = pd.DataFrame(test_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%dT%H:%M:%SZ')

    # Test the GoldLayerProcessor
    processor = GoldLayerProcessor()

    # This should filter out the cross-day record
    result = processor.transform_to_gold('generation', df, '2023-11-06')

    # Should have 2 records (excluding the midnight record from next day)
    # The cross-day record should be filtered out, leaving 2 records grouped by fuel type
    assert len(result) == 2

    # Check that the cross-day record was properly filtered out
    # The result should only contain records from 2023-11-06
    for _, row in result.iterrows():
        # All rows should have the correct date (2023-11-06)
        assert row['date'] == '2023-11-06'


def test_generation_filtering_expected_values():
    """Test that the filtering produces the expected values"""

    # Create test data matching the exact expected result
    test_data = [
        # Records from the correct processing date (2023-11-06)
        {'date': '2023-11-06', 'timestamp': '2023-11-06T00:00:00Z', 'value': 1000, 'fuel_type': 'wind'},
        {'date': '2023-11-06', 'timestamp': '2023-11-06T01:00:00Z', 'value': 1500, 'fuel_type': 'wind'},
        {'date': '2023-11-06', 'timestamp': '2023-11-06T23:00:00Z', 'value': 2000, 'fuel_type': 'wind'},
        {'date': '2023-11-06', 'timestamp': '2023-11-06T12:00:00Z', 'value': 2500, 'fuel_type': 'solar'},
        # Cross-day record that should be excluded
        {'date': '2023-11-06', 'timestamp': '2023-11-07T00:00:00Z', 'value': 3118, 'fuel_type': 'solar'},
    ]

    # Create DataFrame
    df = pd.DataFrame(test_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%dT%H:%M:%SZ')

    # Test the GoldLayerProcessor
    processor = GoldLayerProcessor()

    # Process the data with explicit processing date
    result = processor.transform_to_gold('generation', df, '2023-11-06')

    # Should have 2 records (excluding the cross-day record)
    # Grouped by fuel type
    assert len(result) == 2

    # Check the results are correct
    # Wind: 1000 + 1500 + 2000 = 4500 total, avg = 1500
    # Solar: 2500 total, avg = 2500
    wind_row = result[result['fuel_type'] == 'wind'].iloc[0]
    solar_row = result[result['fuel_type'] == 'solar'].iloc[0]

    assert wind_row['total_generation'] == 4500
    assert wind_row['avg_generation'] == 1500
    assert solar_row['total_generation'] == 2500
    assert solar_row['avg_generation'] == 2500


def test_boundary_record_exclusion():
    """Test that boundary records are properly excluded"""
    # Test the exact scenario from production: 97 records, 96 valid + 1 boundary
    test_data = [
        # 96 records from 2026-11-06
        {'date': '2026-11-06', 'timestamp': '2026-11-06T00:00:00Z', 'value': 1000, 'fuel_type': 'wind'}
        for _ in range(96)
    ] + [
        # 1 boundary record from 2026-11-07 (should be excluded)
        {'date': '2026-11-07', 'timestamp': '2026-11-07T00:00:00Z', 'value': 3118, 'fuel_type': 'solar'}
    ]

    # Create DataFrame
    df = pd.DataFrame(test_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%dT%H:%M:%SZ')

    # Test the GoldLayerProcessor with explicit processing date
    processor = GoldLayerProcessor()

    # Process with explicit processing date 2026-11-06
    result = processor.transform_to_gold('generation', df, '2026-11-06')

    # Should have 96 records (boundary record excluded)
    assert len(result) == 96

    # Verify all records have the correct processing date
    for _, row in result.iterrows():
        assert row['date'] == '2026-11-06'