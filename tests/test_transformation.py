"""
Tests for data transformation components
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import json
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq
from src.transformation.data_transformation import DataTransformer
from src.common.config import Config


def test_data_transformer_initialization():
    """Test DataTransformer initialization"""
    transformer = DataTransformer()
    assert transformer is not None
    assert transformer.config is not None


def test_validate_bronze_data_demand_valid():
    """Test validation of valid demand data"""
    transformer = DataTransformer()
    
    valid_data = {
        'date': '2023-01-01',
        'demand_values': [{'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}]
    }
    
    result = transformer.validate_bronze_data(valid_data, 'demand')
    assert result is True


def test_validate_bronze_data_demand_invalid():
    """Test validation of invalid demand data"""
    transformer = DataTransformer()
    
    invalid_data = {
        'date': '2023-01-01'
        # Missing demand_values
    }
    
    result = transformer.validate_bronze_data(invalid_data, 'demand')
    assert result is False


def test_validate_bronze_data_weather_valid():
    """Test validation of valid weather data"""
    transformer = DataTransformer()
    
    valid_data = {
        'latitude': 53.3498,
        'longitude': -6.2603,
        'hourly': {},
        'daily': {}
    }
    
    result = transformer.validate_bronze_data(valid_data, 'weather')
    assert result is True


@patch('src.transformation.data_transformation.boto3.client')
def test_process_bronze_to_silver(mock_boto_client):
    """Test processing from Bronze to Silver layer"""
    transformer = DataTransformer()
    
    # Mock the S3 client
    mock_s3 = Mock()
    mock_boto_client.return_value = mock_s3
    
    # Mock the BronzeLayerProcessor's S3 client too
    with patch.object(transformer.bronze_processor, 's3_client') as mock_bronze_s3:
        # Mock successful operations
        mock_bronze_s3.get_object.return_value = {'Body': BytesIO(json.dumps({
            'date': '2023-01-01',
            'demand_values': [
                {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
            ]
        }).encode())}
        mock_bronze_s3.put_object.return_value = {}
        
        # Mock the silver processor's S3 client
        with patch.object(transformer.silver_processor, 's3_client') as mock_silver_s3:
            mock_silver_s3.put_object.return_value = {}
            
            # Test with dummy data
            result = transformer.process_bronze_to_silver('demand', '2023-01-01')
            assert result is True  # Should succeed with mock


@patch('src.transformation.data_transformation.boto3.client')
def test_process_silver_to_gold(mock_boto_client):
    """Test processing from Silver to Gold layer"""
    transformer = DataTransformer()
    
    # Mock the S3 client
    mock_s3 = Mock()
    mock_boto_client.return_value = mock_s3
    
    # Mock the SilverLayerProcessor's S3 client too
    with patch.object(transformer.silver_processor, 's3_client') as mock_silver_s3:
        # Mock successful operations - create actual Parquet data
        # Create a simple DataFrame and convert to Parquet
        df = pd.DataFrame({
            'date': ['2023-01-01'],
            'timestamp': [pd.to_datetime('2023-01-01T00:00:00Z')],
            'value': [1000]
        })
        table = pa.Table.from_pandas(df)
        buffer = BytesIO()
        pq.write_table(table, buffer)
        buffer.seek(0)
        
        mock_silver_s3.get_object.return_value = {'Body': buffer}
        mock_silver_s3.put_object.return_value = {}
        
        # Mock the gold processor's S3 client
        with patch.object(transformer.gold_processor, 's3_client') as mock_gold_s3:
            mock_gold_s3.put_object.return_value = {}
            
            # Test with dummy data
            result = transformer.process_silver_to_gold('demand', '2023-01-01')
            assert result is True  # Should succeed with mock


if __name__ == "__main__":
    pytest.main([__file__, "-v"])