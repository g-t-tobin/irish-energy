"""
Integration tests for the complete data pipeline
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import json
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq
from src.transformation.data_transformation import DataTransformer
from src.transformation.quality_checks import QualityChecker
from src.common.config import Config


def test_data_transformer_pipeline_end_to_end():
    """Test complete data transformation pipeline"""
    # Setup
    transformer = DataTransformer()
    
    # Mock the S3 client and all dependent operations
    with patch.object(transformer, 's3_client') as mock_s3, \
         patch.object(transformer.bronze_processor, 's3_client') as mock_bronze_s3, \
         patch.object(transformer.silver_processor, 's3_client') as mock_silver_s3, \
         patch.object(transformer.gold_processor, 's3_client') as mock_gold_s3:
        
        # Mock successful operations
        mock_s3.head_object.return_value = None  # No existing data
        mock_bronze_s3.put_object.return_value = {}
        mock_bronze_s3.get_object.return_value = {'Body': BytesIO(json.dumps({
            'date': '2023-01-01',
            'demand_values': [
                {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
            ]
        }).encode())}
        mock_silver_s3.put_object.return_value = {}
        # Create actual Parquet data for mocking
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
        mock_gold_s3.put_object.return_value = {}
        
        # Test data
        demand_data = {
            'date': '2023-01-01',
            'demand_values': [
                {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
            ]
        }
        
        # Test the full pipeline
        result = transformer.process_data_pipeline('demand', '2023-01-01', demand_data)
        
        # Assertions
        assert result is True


def test_incremental_processing():
    """Test incremental data processing"""
    # Setup
    transformer = DataTransformer()
    
    # Mock the S3 client
    with patch.object(transformer, 's3_client') as mock_s3:
        # Mock that Gold layer data already exists
        mock_s3.head_object.side_effect = lambda Bucket, Key: None  # Simulate object exists
        
        # Test data
        demand_data = {
            'date': '2023-01-01',
            'demand_values': [
                {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
            ]
        }
        
        # Test incremental processing
        result = transformer.process_incremental_data('demand', '2023-01-01', demand_data)
        
        # Assertions
        assert result is True  # Should return True since data already exists


def test_quality_metrics_generation():
    """Test quality metrics generation"""
    # Setup
    transformer = DataTransformer()
    
    # Test metrics generation
    metrics = transformer.get_data_quality_metrics('demand', '2023-01-01')
    
    # Assertions
    assert metrics['data_type'] == 'demand'
    assert metrics['date'] == '2023-01-01'
    assert 'processing_timestamp' in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])