import pytest
import os
import sys
from unittest.mock import Mock, patch
import pandas as pd
from io import BytesIO

# Add the api directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.services.data_service import S3GoldDataRetriever

class TestDataService:
    def test_init_s3_client(self):
        """Test that S3 client is initialized correctly"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
            
            retriever = S3GoldDataRetriever()
            
            # Verify boto3.client was called with correct arguments
            mock_boto_client.assert_called_once_with('s3', region_name='eu-west-1')
            
            # Verify the client instance was stored
            assert retriever.s3_client == mock_client_instance
    
    def test_read_parquet_from_s3_success(self):
        """Test successful reading of parquet file from S3"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
    
            # Create a proper parquet file in memory for testing
            import pandas as pd
            import pyarrow as pa
            from io import BytesIO
            
            # Create sample data
            sample_data = pd.DataFrame({
                'date': ['2023-01-01', '2023-01-02'],
                'value': [100, 200]
            })
            
            # Create parquet buffer
            buffer = BytesIO()
            sample_data.to_parquet(buffer, engine='pyarrow')
            buffer.seek(0)
            
            # Setup mock response
            mock_response = {
                'Body': Mock()
            }
            mock_response['Body'].read.return_value = buffer.getvalue()
            mock_client_instance.get_object.return_value = mock_response
    
            retriever = S3GoldDataRetriever()
    
            # Test the method
            result = retriever._read_parquet_from_s3('test-key')
            
            # Verify the result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert list(result.columns) == ['date', 'value']
            
            # Verify the call was made correctly
            mock_client_instance.get_object.assert_called_once_with(
                Bucket=retriever.bucket_name,
                Key='test-key'
            )
    
    def test_read_parquet_from_s3_error_handling(self):
        """Test error handling when reading from S3 fails"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
            
            # Setup mock to raise an exception
            mock_client_instance.get_object.side_effect = Exception("S3 Error")
            
            retriever = S3GoldDataRetriever()
            
            # Test that exception is raised
            with pytest.raises(Exception):
                retriever._read_parquet_from_s3('test-key')
    
    @patch('api.services.data_service.pd.read_parquet')
    def test_get_demand_data_success(self, mock_read_parquet):
        """Test successful retrieval of demand data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
            
            # Setup mock dataframe
            mock_df = pd.DataFrame({
                'timestamp': ['2023-01-01T00:00:00'],
                'demand_mw': [100.0],
                'demand_mwh': [1000.0],
                'forecast_mw': [110.0],
                'forecast_mwh': [1100.0]
            })
            mock_read_parquet.return_value = mock_df
            
            # Setup mock response
            mock_response = {
                'Body': Mock()
            }
            mock_response['Body'].read.return_value = b'fake parquet data'
            mock_client_instance.get_object.return_value = mock_response
            
            retriever = S3GoldDataRetriever()
            
            # Test the method
            result = retriever.get_demand_data()
            
            # Verify the call was made correctly
            mock_client_instance.get_object.assert_called_once_with(
                Bucket=retriever.bucket_name,
                Key='demand/demand_data.parquet'
            )
            
            # Verify we got the expected result
            assert len(result) == 1
            assert result[0]['demand_mw'] == 100.0
    
    @patch('api.services.data_service.pd.read_parquet')
    def test_get_weather_data_success(self, mock_read_parquet):
        """Test successful retrieval of weather data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
            
            # Setup mock dataframe
            mock_df = pd.DataFrame({
                'timestamp': ['2023-01-01T00:00:00'],
                'temperature_celsius': [15.0],
                'humidity_percent': [70.0],
                'wind_speed_mps': [5.0],
                'wind_direction_degrees': [180.0],
                'pressure_hpa': [1013.0],
                'precipitation_mm': [0.0]
            })
            mock_read_parquet.return_value = mock_df
            
            # Setup mock response
            mock_response = {
                'Body': Mock()
            }
            mock_response['Body'].read.return_value = b'fake parquet data'
            mock_client_instance.get_object.return_value = mock_response
            
            retriever = S3GoldDataRetriever()
            
            # Test the method
            result = retriever.get_weather_data()
            
            # Verify the call was made correctly
            mock_client_instance.get_object.assert_called_once_with(
                Bucket=retriever.bucket_name,
                Key='weather/weather_data.parquet'
            )
            
            # Verify we got the expected result
            assert len(result) == 1
            assert result[0]['temperature_celsius'] == 15.0
    
    @patch('api.services.data_service.pd.read_parquet')
    def test_get_generation_data_success(self, mock_read_parquet):
        """Test successful retrieval of generation data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
            
            # Setup mock dataframe
            mock_df = pd.DataFrame({
                'timestamp': ['2023-01-01T00:00:00'],
                'renewable_generation_mw': [50.0],
                'fossil_generation_mw': [30.0],
                'nuclear_generation_mw': [20.0],
                'total_generation_mw': [100.0]
            })
            mock_read_parquet.return_value = mock_df
            
            # Setup mock response
            mock_response = {
                'Body': Mock()
            }
            mock_response['Body'].read.return_value = b'fake parquet data'
            mock_client_instance.get_object.return_value = mock_response
            
            retriever = S3GoldDataRetriever()
            
            # Test the method
            result = retriever.get_generation_data()
            
            # Verify the call was made correctly
            mock_client_instance.get_object.assert_called_once_with(
                Bucket=retriever.bucket_name,
                Key='generation/generation_data.parquet'
            )
            
            # Verify we got the expected result
            assert len(result) == 1
            assert result[0]['total_generation_mw'] == 100.0
    
    @patch('api.services.data_service.pd.read_parquet')
    def test_get_quality_metrics_success(self, mock_read_parquet):
        """Test successful retrieval of quality metrics"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
            
            # Setup mock dataframe
            mock_df = pd.DataFrame({
                'dataset_name': ['demand'],
                'total_records': [1000],
                'missing_values': [5],
                'data_quality_score': [0.995],
                'last_updated': ['2023-01-01T00:00:00']
            })
            mock_read_parquet.return_value = mock_df
            
            # Setup mock response
            mock_response = {
                'Body': Mock()
            }
            mock_response['Body'].read.return_value = b'fake parquet data'
            mock_client_instance.get_object.return_value = mock_response
            
            retriever = S3GoldDataRetriever()
            
            # Test the method
            result = retriever.get_quality_metrics()
            
            # Verify the call was made correctly
            mock_client_instance.get_object.assert_called_once_with(
                Bucket=retriever.bucket_name,
                Key='quality/data_quality_metrics.parquet'
            )
            
            # Verify we got the expected result
            assert len(result) == 1
            assert result[0]['dataset_name'] == 'demand'
    
    @patch('api.services.data_service.pd.read_parquet')
    def test_get_summary_data_success(self, mock_read_parquet):
        """Test successful retrieval of summary data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance
            
            # Setup mock dataframe
            mock_df = pd.DataFrame({
                'total_datasets': [5],
                'total_records': [10000],
                'last_updated': ['2023-01-01T00:00:00'],
                'data_quality_summary': ['{"avg_score": 0.99}']
            })
            mock_read_parquet.return_value = mock_df
            
            # Setup mock response
            mock_response = {
                'Body': Mock()
            }
            mock_response['Body'].read.return_value = b'fake parquet data'
            mock_client_instance.get_object.return_value = mock_response
            
            retriever = S3GoldDataRetriever()
            
            # Test the method
            result = retriever.get_summary_data()
            
            # Verify the call was made correctly
            mock_client_instance.get_object.assert_called_once_with(
                Bucket=retriever.bucket_name,
                Key='summary/summary_data.parquet'
            )
            
            # Verify we got the expected result
            assert result['total_datasets'] == 5
            assert result['total_records'] == 10000