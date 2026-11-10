"""
Integration tests for retry logic in transformation pipeline
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import json
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq
from src.transformation.data_transformation import DataTransformer
from src.transformation.retry_logic import RetryConfig, CircuitBreaker
from src.common.config import Config


class TestDataTransformerRetryIntegration:
    """Test retry integration in DataTransformer"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.transformer = DataTransformer()
        
    @patch('src.transformation.data_transformation.boto3.client')
    def test_process_bronze_layer_retry_success(self, mock_boto_client):
        """Test successful bronze layer processing with retry"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock successful storage
        mock_s3.put_object.return_value = {}
        
        # Test with valid data
        raw_data = {
            'date': '2023-01-01',
            'demand_values': [{'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}]
        }
        
        success = self.transformer.process_bronze_layer('demand', '2023-01-01', raw_data)
        assert success is True

    @patch('src.transformation.data_transformation.boto3.client')
    def test_process_bronze_layer_retry_failure(self, mock_boto_client):
        """Test bronze layer processing failure with retry"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock failing storage operation
        mock_s3.put_object.side_effect = Exception("S3 connection failed")
        
        # Test with valid data
        raw_data = {
            'date': '2023-01-01',
            'demand_values': [{'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}]
        }
        
        # Should fail after retries are exhausted
        success = self.transformer.process_bronze_layer('demand', '2023-01-01', raw_data)
        assert success is False

    @patch('src.transformation.data_transformation.boto3.client')
    def test_process_data_pipeline_retry_integration(self, mock_boto_client):
        """Test full pipeline retry integration"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3
        
        # Mock successful operations
        mock_s3.put_object.return_value = {}
        mock_s3.get_object.return_value = {'Body': BytesIO(json.dumps({
            'date': '2023-01-01',
            'demand_values': [
                {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
            ]
        }).encode())}
        
        # Test with valid data
        raw_data = {
            'date': '2023-01-01',
            'demand_values': [{'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}]
        }
        
        # Should succeed with all layers
        success = self.transformer.process_data_pipeline('demand', '2023-01-01', raw_data)
        assert success is True

    @patch('src.transformation.data_transformation.boto3.client')
    def test_retry_config_integration(self, mock_boto_client):
        """Test that retry configuration is properly integrated"""
        assert self.transformer.retry_config is not None
        assert self.transformer.circuit_breaker is not None
        
        # Test retry config values
        assert self.transformer.retry_config.max_attempts == 3
        assert self.transformer.retry_config.base_delay == 1.0
        assert self.transformer.retry_config.max_delay == 60.0
        assert self.transformer.retry_config.backoff_factor == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])