"""
Tests for Gold transformation service
"""

import pytest
import pandas as pd
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import uuid

from src.transformation.gold_transformation import (
    GoldTransformationService,
    GoldTransformationStatus
)
from src.common.config import Config


def test_gold_transformation_service_initialization():
    """Test GoldTransformationService initialization"""
    transformer = GoldTransformationService('local')
    assert transformer is not None
    assert transformer.config is not None
    assert transformer.quality_checker is not None


def test_transform_demand_to_gold_valid():
    """Test demand data transformation with valid data"""
    transformer = GoldTransformationService('local')

    # Create sample Silver demand data
    silver_df = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-01', '2023-01-01'],
        'timestamp': pd.to_datetime([
            '2023-01-01T00:00:00Z',
            '2023-01-01T01:00:00Z',
            '2023-01-01T02:00:00Z'
        ]),
        'value': [1000, 1050, 980],
        'source': ['EirGrid', 'EirGrid', 'EirGrid'],
        'ingestion_id': ['ingest-123', 'ingest-123', 'ingest-123']
    })

    result = transformer._transform_demand_to_gold(silver_df)
    assert result is not None
    assert len(result) == 1  # Should group by date

    # Check first record
    record1 = result.iloc[0]
    assert record1['date'] == '2023-01-01'
    assert record1['total_demand'] == 3030.0  # 1000 + 1050 + 980
    assert record1['avg_demand'] == 1010.0  # 3030 / 3
    assert record1['min_demand'] == 980.0
    assert record1['max_demand'] == 1050.0
    assert record1['record_count'] == 3


def test_transform_weather_to_gold_valid():
    """Test weather data transformation with valid data"""
    transformer = GoldTransformationService('local')

    # Create sample Silver weather data
    silver_df = pd.DataFrame({
        'latitude': [53.3498, 53.3498],
        'longitude': [-6.2603, -6.2603],
        'timestamp': pd.to_datetime([
            '2023-01-01T00:00:00Z',
            '2023-01-01T01:00:00Z'
        ]),
        'temperature': [5.2, 5.5],
        'wind_speed': [3.2, 3.8],
        'source': ['Open-Meteo', 'Open-Meteo'],
        'ingestion_id': ['ingest-123', 'ingest-123']
    })

    result = transformer._transform_weather_to_gold(silver_df)
    assert result is not None
    assert len(result) == 1  # Should group by date

    # Check first record
    record1 = result.iloc[0]
    assert record1['date'] == '2023-01-01'
    assert record1['avg_temperature'] == 5.35  # (5.2 + 5.5) / 2
    assert record1['min_temperature'] == 5.2
    assert record1['max_temperature'] == 5.5
    assert record1['avg_wind_speed'] == 3.5  # (3.2 + 3.8) / 2


def test_transform_generation_to_gold_valid():
    """Test generation data transformation with valid data"""
    transformer = GoldTransformationService('local')

    # Create sample Silver generation data
    silver_df = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-01', '2023-01-01'],
        'timestamp': pd.to_datetime([
            '2023-01-01T00:00:00Z',
            '2023-01-01T01:00:00Z',
            '2023-01-01T02:00:00Z'
        ]),
        'value': [1500, 1600, 1400],
        'fuel_type': ['wind', 'solar', 'wind'],
        'source': ['EirGrid', 'EirGrid', 'EirGrid'],
        'ingestion_id': ['ingest-123', 'ingest-123', 'ingest-123']
    })

    result = transformer._transform_generation_to_gold(silver_df)
    assert result is not None
    assert len(result) == 2  # Should group by date and fuel type

    # Check records
    wind_record = result[result['fuel_type'] == 'wind'].iloc[0]
    solar_record = result[result['fuel_type'] == 'solar'].iloc[0]

    assert wind_record['date'] == '2023-01-01'
    assert wind_record['fuel_type'] == 'wind'
    assert wind_record['total_generation'] == 2900.0  # 1500 + 1400
    assert wind_record['avg_generation'] == 1450.0  # 2900 / 2
    assert wind_record['record_count'] == 2

    assert solar_record['date'] == '2023-01-01'
    assert solar_record['fuel_type'] == 'solar'
    assert solar_record['total_generation'] == 1600.0
    assert solar_record['avg_generation'] == 1600.0
    assert solar_record['record_count'] == 1


def test_validate_silver_schema_valid():
    """Test validation of valid Silver data schema"""
    transformer = GoldTransformationService('local')

    # Create valid demand data
    df = pd.DataFrame({
        'date': ['2023-01-01'],
        'timestamp': pd.to_datetime(['2023-01-01T00:00:00Z']),
        'value': [1000.0],
        'source': ['EirGrid'],
        'ingestion_id': ['test-ingest-123']
    })

    result = transformer._validate_silver_schema(df, 'demand')
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_silver_schema_invalid():
    """Test validation of invalid Silver data schema"""
    transformer = GoldTransformationService('local')

    # Create invalid data (missing value column)
    df = pd.DataFrame({
        'date': ['2023-01-01'],
        'timestamp': pd.to_datetime(['2023-01-01T00:00:00Z']),
        'source': ['EirGrid'],
        'ingestion_id': ['test-ingest-123']
    })

    result = transformer._validate_silver_schema(df, 'demand')
    assert result['valid'] is False
    assert len(result['errors']) > 0


def test_validate_gold_schema_valid():
    """Test validation of valid Gold data schema"""
    transformer = GoldTransformationService('local')

    # Create valid Gold demand data
    df = pd.DataFrame({
        'date': ['2023-01-01'],
        'total_demand': [1000.0],
        'avg_demand': [1000.0],
        'min_demand': [1000.0],
        'max_demand': [1000.0],
        'record_count': [1]
    })

    result = transformer._validate_gold_schema(df, 'demand')
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_gold_schema_invalid():
    """Test validation of invalid Gold data schema"""
    transformer = GoldTransformationService('local')

    # Create invalid data (missing required column)
    df = pd.DataFrame({
        'date': ['2023-01-01'],
        'total_demand': [1000.0],
        'avg_demand': [1000.0],
        'min_demand': [1000.0],
        'record_count': [1]
        # Missing max_demand column
    })

    result = transformer._validate_gold_schema(df, 'demand')
    assert result['valid'] is False
    assert len(result['errors']) > 0


def test_get_aggregation_counts():
    """Test aggregation counts calculation"""
    transformer = GoldTransformationService('local')

    # Test demand data
    df_demand = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-01'],
        'total_demand': [1000.0, 1500.0],
        'avg_demand': [1000.0, 1500.0],
        'min_demand': [1000.0, 1500.0],
        'max_demand': [1000.0, 1500.0],
        'record_count': [1, 1]
    })

    counts = transformer._get_aggregation_counts(df_demand, 'demand')
    assert counts['total_records'] == 2

    # Test generation data
    df_gen = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-01'],
        'fuel_type': ['wind', 'solar'],
        'total_generation': [1000.0, 1500.0],
        'avg_generation': [1000.0, 1500.0],
        'record_count': [1, 1]
    })

    counts = transformer._get_aggregation_counts(df_gen, 'generation')
    assert 'by_fuel_type' in counts


def test_calculate_quality_score():
    """Test quality score calculation"""
    transformer = GoldTransformationService('local')

    # Create data with no missing values
    df = pd.DataFrame({
        'date': ['2023-01-01'],
        'total_demand': [1000.0],
        'avg_demand': [1000.0],
        'min_demand': [1000.0],
        'max_demand': [1000.0],
        'record_count': [1]
    })

    score = transformer._calculate_quality_score(df, df)
    assert score == 100.0  # Perfect quality

    # Create data with missing values
    df_with_nulls = pd.DataFrame({
        'date': ['2023-01-01', '2023-01-01'],
        'total_demand': [1000.0, None],
        'avg_demand': [1000.0, 1000.0],
        'min_demand': [1000.0, 1000.0],
        'max_demand': [1000.0, 1000.0],
        'record_count': [1, 1]
    })

    score = transformer._calculate_quality_score(df_with_nulls, df_with_nulls)
    assert score < 100.0  # Reduced quality due to missing values


def test_save_gold_data_to_storage():
    """Test saving Gold data to storage"""
    transformer = GoldTransformationService('local')

    # Create sample data
    df = pd.DataFrame({
        'date': ['2023-01-01'],
        'total_demand': [1000.0],
        'avg_demand': [1000.0],
        'min_demand': [1000.0],
        'max_demand': [1000.0],
        'record_count': [1]
    })

    # This should work without throwing errors
    saved = transformer._save_gold_data_to_storage(df, 'demand', '2023-01-01')
    assert saved is True  # Will be True since we're mocking storage


def test_get_gold_processing_summary():
    """Test getting Gold processing summary"""
    transformer = GoldTransformationService('local')

    summary = transformer.get_gold_processing_summary('demand', '2023-01-01')

    assert summary['data_type'] == 'demand'
    assert summary['date'] == '2023-01-01'
    assert 'timestamp' in summary
    assert summary['silver_processed'] is True
    assert summary['gold_processed'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])