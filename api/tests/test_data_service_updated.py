import pytest
import os
import sys
from unittest.mock import Mock, patch
import pandas as pd
from io import BytesIO
import pyarrow as pa

# Add the api directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.services.data_service import S3GoldDataRetriever, GoldDataNotFoundError, GoldDataParseError


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

    def test_list_gold_keys_success(self):
        """Test successful listing of Gold keys"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock response
            mock_response = {
                'Contents': [
                    {'Key': 'demand/gold/2026-11-06.parquet'},
                    {'Key': 'demand/gold/2026-11-05.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response]

            retriever = S3GoldDataRetriever()

            # Test the method
            result = retriever._list_gold_keys('demand')

            # Verify result
            assert result == ['demand/gold/2026-11-05.parquet', 'demand/gold/2026-11-06.parquet']

    def test_read_parquet_from_s3_success(self):
        """Test successful reading of parquet file from S3"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Create a proper parquet file in memory for testing
            sample_data = pd.DataFrame({
                'date': ['2026-11-06', '2026-11-05'],
                'total_demand': [1000.0, 950.0],
                'avg_demand': [980.0, 930.0],
                'min_demand': [900.0, 850.0],
                'max_demand': [1100.0, 1050.0]
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
            result = retriever._read_parquet_from_s3('demand/gold/2026-11-06.parquet')

            # Verify the result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert list(result.columns) == ['date', 'total_demand', 'avg_demand', 'min_demand', 'max_demand']

            # Verify the call was made correctly
            mock_client_instance.get_object.assert_called_once_with(
                Bucket=retriever.bucket_name,
                Key='demand/gold/2026-11-06.parquet'
            )

    def test_read_parquet_from_s3_not_found(self):
        """Test error handling when parquet file is not found"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock to raise a ClientError with NoSuchKey error code
            from botocore.exceptions import ClientError
            mock_client_instance.get_object.side_effect = ClientError(
                error_response={'Error': {'Code': 'NoSuchKey'}},
                operation_name='GetObject'
            )

            retriever = S3GoldDataRetriever()

            # Test that GoldDataNotFoundError is raised
            with pytest.raises(GoldDataNotFoundError):
                retriever._read_parquet_from_s3('demand/gold/2026-11-06.parquet')

    def test_load_dataset_empty_result(self):
        """Test loading dataset when no keys are found"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock response for empty list
            mock_response = {'Contents': []}
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response]

            retriever = S3GoldDataRetriever()

            # Test that GoldDataNotFoundError is raised for required dataset
            with pytest.raises(GoldDataNotFoundError):
                retriever._load_dataset('demand', required=True)

            # Test that None is returned for non-required dataset
            result = retriever._load_dataset('demand', required=False)
            assert result is None

    def test_load_dataset_multiple_partitions(self):
        """Test loading dataset with multiple date partitions"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock responses for multiple parquet files
            mock_response1 = {
                'Contents': [
                    {'Key': 'demand/gold/2026-11-06.parquet'},
                    {'Key': 'demand/gold/2026-11-05.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response1]

            # Create sample data for first parquet
            sample_data1 = pd.DataFrame({
                'date': ['2026-11-06', '2026-11-05'],
                'total_demand': [1000.0, 950.0],
                'avg_demand': [980.0, 930.0],
                'min_demand': [900.0, 850.0],
                'max_demand': [1100.0, 1050.0]
            })

            # Create sample data for second parquet
            sample_data2 = pd.DataFrame({
                'date': ['2026-11-04', '2026-11-03'],
                'total_demand': [900.0, 850.0],
                'avg_demand': [880.0, 830.0],
                'min_demand': [800.0, 750.0],
                'max_demand': [1000.0, 950.0]
            })

            # Create parquet buffers
            buffer1 = BytesIO()
            sample_data1.to_parquet(buffer1, engine='pyarrow')
            buffer1.seek(0)

            buffer2 = BytesIO()
            sample_data2.to_parquet(buffer2, engine='pyarrow')
            buffer2.seek(0)

            # Setup mock responses for get_object
            mock_response_obj1 = {'Body': Mock()}
            mock_response_obj1['Body'].read.return_value = buffer1.getvalue()
            mock_response_obj2 = {'Body': Mock()}
            mock_response_obj2['Body'].read.return_value = buffer2.getvalue()

            mock_client_instance.get_object.side_effect = [mock_response_obj1, mock_response_obj2]

            retriever = S3GoldDataRetriever()

            # Test loading dataset
            result = retriever._load_dataset('demand')

            # Verify the result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 4  # All dates combined
            assert list(result.columns) == ['date', 'total_demand', 'avg_demand', 'min_demand', 'max_demand']

    def test_load_dataset_with_date_filtering(self):
        """Test loading dataset with date filtering"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock responses for multiple parquet files
            mock_response1 = {
                'Contents': [
                    {'Key': 'demand/gold/2026-11-06.parquet'},
                    {'Key': 'demand/gold/2026-11-05.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response1]

            # Create sample data
            sample_data = pd.DataFrame({
                'date': ['2026-11-06', '2026-11-05'],
                'total_demand': [1000.0, 950.0],
                'avg_demand': [980.0, 930.0],
                'min_demand': [900.0, 850.0],
                'max_demand': [1100.0, 1050.0]
            })

            # Create parquet buffer
            buffer = BytesIO()
            sample_data.to_parquet(buffer, engine='pyarrow')
            buffer.seek(0)

            # Setup mock response for get_object
            mock_response_obj = {'Body': Mock()}
            mock_response_obj['Body'].read.return_value = buffer.getvalue()
            mock_client_instance.get_object.return_value = mock_response_obj

            retriever = S3GoldDataRetriever()

            # Test loading dataset with date filtering
            result = retriever._load_dataset('demand', start_date='2026-11-06', end_date='2026-11-06')

            # Verify the result - should only include 2026-11-06
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert result.iloc[0]['date'].strftime('%Y-%m-%d') == '2026-11-06'

    def test_load_dataset_invalid_date_format(self):
        """Test error handling with invalid date formats"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            retriever = S3GoldDataRetriever()

            # Test invalid start date
            with pytest.raises(Exception):
                retriever._load_dataset('demand', start_date='invalid-date')

            # Test invalid end date
            with pytest.raises(Exception):
                retriever._load_dataset('demand', end_date='invalid-date')

    def test_get_demand_data_success(self):
        """Test successful retrieval of demand data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock response for list_objects
            mock_response = {
                'Contents': [
                    {'Key': 'demand/gold/2026-11-06.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response]

            # Create sample data
            sample_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'total_demand': [1000.0],
                'avg_demand': [980.0],
                'min_demand': [900.0],
                'max_demand': [1100.0]
            })

            # Create parquet buffer
            buffer = BytesIO()
            sample_data.to_parquet(buffer, engine='pyarrow')
            buffer.seek(0)

            # Setup mock response for get_object
            mock_response_obj = {'Body': Mock()}
            mock_response_obj['Body'].read.return_value = buffer.getvalue()
            mock_client_instance.get_object.return_value = mock_response_obj

            retriever = S3GoldDataRetriever()

            # Test the method
            result = retriever.get_demand_data()

            # Verify the result
            assert len(result) == 1
            assert result[0]['date'] == '2026-11-06'
            assert result[0]['total_demand'] == 1000.0

    def test_get_weather_data_success(self):
        """Test successful retrieval of weather data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock response for list_objects
            mock_response = {
                'Contents': [
                    {'Key': 'weather/gold/2026-11-06.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response]

            # Create sample data
            sample_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'avg_temperature': [15.0],
                'min_temperature': [10.0],
                'max_temperature': [20.0],
                'avg_humidity': [70.0]
            })

            # Create parquet buffer
            buffer = BytesIO()
            sample_data.to_parquet(buffer, engine='pyarrow')
            buffer.seek(0)

            # Setup mock response for get_object
            mock_response_obj = {'Body': Mock()}
            mock_response_obj['Body'].read.return_value = buffer.getvalue()
            mock_client_instance.get_object.return_value = mock_response_obj

            retriever = S3GoldDataRetriever()

            # Test the method
            result = retriever.get_weather_data()

            # Verify the result
            assert len(result) == 1
            assert result[0]['date'] == '2026-11-06'
            assert result[0]['avg_temperature'] == 15.0

    def test_get_generation_data_success(self):
        """Test successful retrieval of generation data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock response for list_objects
            mock_response = {
                'Contents': [
                    {'Key': 'generation/gold/2026-11-06.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response]

            # Create sample data with fuel_type
            sample_data = pd.DataFrame({
                'date': ['2026-11-06', '2026-11-06'],
                'total_generation': [500.0, 300.0],
                'avg_generation': [480.0, 280.0],
                'fuel_type': ['renewable', 'fossil']
            })

            # Create parquet buffer
            buffer = BytesIO()
            sample_data.to_parquet(buffer, engine='pyarrow')
            buffer.seek(0)

            # Setup mock response for get_object
            mock_response_obj = {'Body': Mock()}
            mock_response_obj['Body'].read.return_value = buffer.getvalue()
            mock_client_instance.get_object.return_value = mock_response_obj

            retriever = S3GoldDataRetriever()

            # Test the method
            result = retriever.get_generation_data()

            # Verify the result
            assert len(result) == 2
            assert result[0]['date'] == '2026-11-06'
            assert result[0]['fuel_type'] in ['renewable', 'fossil']

    def test_get_quality_metrics_success(self):
        """Test successful retrieval of quality metrics"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock response for list_objects
            mock_response = {
                'Contents': [
                    {'Key': 'demand/gold/2026-11-06.parquet'},
                    {'Key': 'weather/gold/2026-11-06.parquet'},
                    {'Key': 'generation/gold/2026-11-06.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response]

            # Create sample data for demand
            demand_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'total_demand': [1000.0],
                'avg_demand': [980.0],
                'min_demand': [900.0],
                'max_demand': [1100.0]
            })

            # Create sample data for weather
            weather_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'avg_temperature': [15.0],
                'min_temperature': [10.0],
                'max_temperature': [20.0],
                'avg_humidity': [70.0]
            })

            # Create sample data for generation
            generation_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'total_generation': [800.0],
                'avg_generation': [780.0],
                'fuel_type': ['total']
            })

            # Create parquet buffers
            buffers = []
            for data in [demand_data, weather_data, generation_data]:
                buffer = BytesIO()
                data.to_parquet(buffer, engine='pyarrow')
                buffer.seek(0)
                buffers.append(buffer.getvalue())

            # Setup mock response for get_object
            mock_client_instance.get_object.side_effect = [mock_response_obj for mock_response_obj in buffers]

            retriever = S3GoldDataRetriever()

            # Test the method
            result = retriever.get_quality_metrics()

            # Verify the result
            assert len(result) == 3  # Should have metrics for all three datasets
            assert result[0]["dataset_name"] in ["demand", "weather", "generation"]

    def test_get_summary_data_success(self):
        """Test successful retrieval of summary data"""
        with patch('api.services.data_service.boto3.client') as mock_boto_client:
            mock_client_instance = Mock()
            mock_boto_client.return_value = mock_client_instance

            # Setup mock response for list_objects
            mock_response = {
                'Contents': [
                    {'Key': 'demand/gold/2026-11-06.parquet'},
                    {'Key': 'weather/gold/2026-11-06.parquet'},
                    {'Key': 'generation/gold/2026-11-06.parquet'}
                ]
            }
            mock_client_instance.get_paginator.return_value.paginate.return_value = [mock_response]

            # Create sample data for demand
            demand_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'total_demand': [1000.0],
                'avg_demand': [980.0],
                'min_demand': [900.0],
                'max_demand': [1100.0]
            })

            # Create sample data for weather
            weather_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'avg_temperature': [15.0],
                'min_temperature': [10.0],
                'max_temperature': [20.0],
                'avg_humidity': [70.0]
            })

            # Create sample data for generation
            generation_data = pd.DataFrame({
                'date': ['2026-11-06'],
                'total_generation': [800.0],
                'avg_generation': [780.0],
                'fuel_type': ['total']
            })

            # Create parquet buffers
            buffers = []
            for data in [demand_data, weather_data, generation_data]:
                buffer = BytesIO()
                data.to_parquet(buffer, engine='pyarrow')
                buffer.seek(0)
                buffers.append(buffer.getvalue())

            # Setup mock response for get_object
            mock_client_instance.get_object.side_effect = [mock_response_obj for mock_response_obj in buffers]

            retriever = S3GoldDataRetriever()

            # Test the method
            result = retriever.get_summary_data()

            # Verify the result
            assert result["total_datasets"] == 3
            assert result["total_records"] > 0
            assert "data_quality_summary" in result