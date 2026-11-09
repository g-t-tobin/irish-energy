"""
Tests for Silver transformation service
"""

import pytest
import pandas as pd
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import uuid

from src.transformation.silver_transformation import (
    SilverTransformationService,
    TransformationStatus,
    QuarantineReason
)
from src.common.config import Config


def test_silver_transformation_service_initialization():
    """Test SilverTransformationService initialization"""
    transformer = SilverTransformationService('local')
    assert transformer is not None
    assert transformer.config is not None
    assert transformer.quality_checker is not None


def test_transform_demand_to_silver_valid():
    """Test demand data transformation with valid data"""
    transformer = SilverTransformationService('local')

    raw_data = {
        'date': '2023-01-01',
        'demand_values': [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000},
            {'timestamp': '2023-01-01T01:00:00Z', 'value': 1050}
        ],
        'source': 'EirGrid',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    metadata = {
        'source': 'EirGrid',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_type': 'demand'
    }

    result = transformer._transform_demand_to_silver(raw_data, metadata)
    assert result is not None
    assert len(result) == 2

    # Check first record
    record1 = result[0]
    assert record1['date'] == '2023-01-01'
    assert record1['value'] == 1000.0
    assert record1['source'] == 'EirGrid'
    assert record1['ingestion_id'] == 'test-ingest-123'


def test_transform_demand_to_silver_invalid():
    """Test demand data transformation with invalid data"""
    transformer = SilverTransformationService('local')

    # Test with missing required fields
    raw_data = {
        'date': '2023-01-01',
        'demand_values': [
            {'timestamp': '2023-01-01T00:00:00Z'}  # Missing value
        ]
    }

    metadata = {
        'source': 'EirGrid',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_type': 'demand'
    }

    result = transformer._transform_demand_to_silver(raw_data, metadata)
    assert result is not None
    assert len(result) == 0  # Should return empty list due to invalid data


def test_transform_weather_to_silver_valid():
    """Test weather data transformation with valid data"""
    transformer = SilverTransformationService('local')

    raw_data = {
        'latitude': 53.3498,
        'longitude': -6.2603,
        'hourly': {
            'time': ['2023-01-01T00:00:00Z', '2023-01-01T01:00:00Z'],
            'temperature_2m': [5.2, 5.5],
            'wind_speed_10m': [3.2, 3.8]
        },
        'daily': {},
        'source': 'Open-Meteo',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    metadata = {
        'source': 'Open-Meteo',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_type': 'weather',
        'location': '53.3498_-6.2603'
    }

    result = transformer._transform_weather_to_silver(raw_data, metadata)
    assert result is not None
    assert len(result) == 2

    # Check first record
    record1 = result[0]
    assert record1['latitude'] == 53.3498
    assert record1['longitude'] == -6.2603
    assert record1['temperature'] == 5.2
    assert record1['wind_speed'] == 3.2
    assert record1['source'] == 'Open-Meteo'
    assert record1['ingestion_id'] == 'test-ingest-123'


def test_transform_generation_to_silver_valid():
    """Test generation data transformation with valid data"""
    transformer = SilverTransformationService('local')

    raw_data = {
        'date': '2023-01-01',
        'generation_values': [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1500, 'fuel_type': 'wind'},
            {'timestamp': '2023-01-01T01:00:00Z', 'value': 1600, 'fuel_type': 'solar'}
        ],
        'source': 'EirGrid',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    metadata = {
        'source': 'EirGrid',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_type': 'generation'
    }

    result = transformer._transform_generation_to_silver(raw_data, metadata)
    assert result is not None
    assert len(result) == 2

    # Check first record
    record1 = result[0]
    assert record1['date'] == '2023-01-01'
    assert record1['value'] == 1500.0
    assert record1['fuel_type'] == 'wind'
    assert record1['source'] == 'EirGrid'
    assert record1['ingestion_id'] == 'test-ingest-123'


def test_validate_transformed_data_valid():
    """Test validation of valid transformed data"""
    transformer = SilverTransformationService('local')

    valid_data = [
        {
            'date': '2023-01-01',
            'timestamp': '2023-01-01T00:00:00Z',
            'value': 1000.0,
            'source': 'EirGrid',
            'ingestion_id': 'test-ingest-123'
        }
    ]

    result = transformer._validate_transformed_data(valid_data, 'demand')
    assert result['valid'] is True
    assert len(result['errors']) == 0


def test_validate_transformed_data_invalid():
    """Test validation of invalid transformed data"""
    transformer = SilverTransformationService('local')

    invalid_data = [
        {
            'timestamp': '2023-01-01T00:00:00Z',
            'value': 1000.0  # Missing required 'date' field
        }
    ]

    result = transformer._validate_transformed_data(invalid_data, 'demand')
    assert result['valid'] is False
    assert len(result['errors']) > 0


def test_generate_record_hash():
    """Test record hash generation for duplicate detection"""
    transformer = SilverTransformationService('local')

    record1 = {
        'date': '2023-01-01',
        'timestamp': '2023-01-01T00:00:00Z',
        'value': 1000.0,
        'source': 'EirGrid'
    }

    # Create a slightly different record to ensure they have different hashes
    record2 = {
        'date': '2023-01-01',
        'timestamp': '2023-01-01T00:00:00Z',
        'value': 1000.0,
        'source': 'EirGrid',
        'different_field': 'different_value'  # Extra field to differentiate
    }

    hash1 = transformer._generate_record_hash(record1)
    hash2 = transformer._generate_record_hash(record2)

    # Different records should have different hashes
    assert hash1 != hash2

    # Same record should have same hash
    hash1_again = transformer._generate_record_hash(record1)
    assert hash1 == hash1_again


def test_create_quarantine_record():
    """Test creation of quarantine records"""
    transformer = SilverTransformationService('local')

    raw_data = {
        'date': '2023-01-01',
        'demand_values': [{'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}]
    }

    metadata = {
        'source': 'EirGrid',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_type': 'demand'
    }

    quarantine_record = transformer._create_quarantine_record(
        raw_data, metadata,
        QuarantineReason.MISSING_VALUE.value,
        "Missing required value field"
    )

    assert quarantine_record['quarantine_reason'] == QuarantineReason.MISSING_VALUE.value
    assert quarantine_record['error_message'] == "Missing required value field"
    assert quarantine_record['original_bronze_source'] == 'EirGrid'
    assert quarantine_record['original_bronze_ingestion_id'] == 'test-ingest-123'
    assert 'quarantine_timestamp' in quarantine_record
    assert 'quarantine_id' in quarantine_record


@patch('src.transformation.silver_transformation.datetime')
def test_add_lineage_metadata(mock_datetime):
    """Test adding lineage metadata to records"""
    mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    transformer = SilverTransformationService('local')

    record = {
        'date': '2023-01-01',
        'timestamp': '2023-01-01T00:00:00Z',
        'value': 1000.0
    }

    metadata = {
        'source': 'EirGrid',
        'ingestion_id': 'test-ingest-123',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data_type': 'demand'
    }

    enhanced_record = transformer._add_lineage_metadata(record, metadata, 'demand')

    assert enhanced_record['source'] == 'EirGrid'
    assert enhanced_record['dataset'] == 'demand'
    assert enhanced_record['bronze_ingestion_id'] == 'test-ingest-123'
    assert enhanced_record['silver_transformation_version'] == '1.0'
    assert enhanced_record['silver_transformation_timestamp'] == '2023-01-01T12:00:00+00:00'


def test_get_transformation_summary():
    """Test getting transformation summary"""
    transformer = SilverTransformationService('local')

    summary = transformer.get_transformation_summary('demand', '2023-01-01')

    assert summary['data_type'] == 'demand'
    assert summary['date'] == '2023-01-01'
    assert 'timestamp' in summary
    assert summary['bronze_processed'] is True
    assert summary['silver_processed'] is True
    assert summary['quarantine_processed'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])