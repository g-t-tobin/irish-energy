"""
Tests for data quality checking components
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import json
from src.transformation.quality_checks import QualityChecker
from src.common.config import Config


def test_quality_checker_initialization():
    """Test QualityChecker initialization"""
    checker = QualityChecker()
    assert checker is not None
    assert checker.config is not None


def test_validate_bronze_data_demand_valid():
    """Test validation of valid demand data"""
    checker = QualityChecker()
    
    valid_data = {
        'date': '2023-01-01',
        'demand_values': [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
        ]
    }
    
    result = checker.validate_bronze_data(valid_data, 'demand')
    assert result is True


def test_validate_bronze_data_demand_invalid_missing_date():
    """Test validation of invalid demand data (missing date)"""
    checker = QualityChecker()
    
    invalid_data = {
        'demand_values': [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
        ]
    }
    
    result = checker.validate_bronze_data(invalid_data, 'demand')
    assert result is False


def test_validate_bronze_data_demand_invalid_bad_date_format():
    """Test validation of invalid demand data (bad date format)"""
    checker = QualityChecker()
    
    invalid_data = {
        'date': '01-01-2023',  # Wrong format
        'demand_values': [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
        ]
    }
    
    result = checker.validate_bronze_data(invalid_data, 'demand')
    assert result is False


def test_validate_bronze_data_weather_valid():
    """Test validation of valid weather data"""
    checker = QualityChecker()
    
    valid_data = {
        'latitude': 53.3498,
        'longitude': -6.2603,
        'hourly': {},
        'daily': {}
    }
    
    result = checker.validate_bronze_data(valid_data, 'weather')
    assert result is True


def test_validate_bronze_data_weather_invalid_missing_fields():
    """Test validation of invalid weather data (missing fields)"""
    checker = QualityChecker()
    
    invalid_data = {
        'latitude': 53.3498,
        # Missing longitude, hourly, daily
    }
    
    result = checker.validate_bronze_data(invalid_data, 'weather')
    assert result is False


def test_validate_bronze_data_generation_valid():
    """Test validation of valid generation data"""
    checker = QualityChecker()
    
    valid_data = {
        'date': '2023-01-01',
        'generation_values': [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000, 'fuel_type': 'wind'}
        ]
    }
    
    result = checker.validate_bronze_data(valid_data, 'generation')
    assert result is True


def test_validate_silver_data_demand_valid():
    """Test validation of valid demand data at Silver layer"""
    checker = QualityChecker()
    
    # Create a proper DataFrame with valid data
    df = pd.DataFrame({
        'date': ['2023-01-01'],
        'timestamp': pd.to_datetime(['2023-01-01T00:00:00Z']),
        'value': [1000]
    })
    
    result = checker.validate_silver_data(df, 'demand')
    assert result is True


@patch('src.transformation.quality_checks.pd.DataFrame')
def test_generate_quality_report(mock_dataframe):
    """Test quality report generation"""
    checker = QualityChecker()
    
    data = {
        'date': '2023-01-01',
        'demand_values': [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
        ]
    }
    
    report = checker.generate_quality_report('demand', data)
    assert report['data_type'] == 'demand'
    assert 'timestamp' in report
    assert report['validation_passed'] is True
    assert report['data_size'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])