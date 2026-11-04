"""
Tests for the transformation Lambda handler
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.transformation.handler import lambda_handler, process_eirgrid_data, process_openmeteo_data


def test_eirgrid_event_processes_demand_and_generation():
    """Test that EirGrid event processes both demand and generation"""
    # Mock event
    event = {
        "source": "custom.eirgrid",
        "detail": {
            "data_type": "eirgrid",
            "date_range": "2023-01-01 to 2023-01-01"
        }
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'demand/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify both demand and generation were processed
        assert mock_transformer.process_incremental_data.call_count == 2
        calls = mock_transformer.process_incremental_data.call_args_list
        assert any(call[0][0] == 'demand' for call in calls)
        assert any(call[0][0] == 'generation' for call in calls)


def test_eirgrid_date_range_processes_all_dates():
    """Test that EirGrid date range processes all dates inclusively"""
    # Mock event with date range spanning multiple days
    event = {
        "source": "custom.eirgrid",
        "detail": {
            "data_type": "eirgrid",
            "date_range": "2023-01-01 to 2023-01-03"
        }
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'demand/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'},
            {'Key': 'demand/2023-01-02/some_file.json', 'LastModified': '2023-01-02T00:00:00Z'},
            {'Key': 'demand/2023-01-03/some_file.json', 'LastModified': '2023-01-03T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify all three dates were processed (demand and generation each)
        assert mock_transformer.process_incremental_data.call_count == 6  # 3 dates * 2 types


def test_openmeteo_event_maps_to_weather():
    """Test that Open-Meteo event maps to weather data type"""
    event = {
        "source": "custom.openmeteo",
        "detail": {
            "data_type": "openmeteo",
            "location": "Dublin",
            "date_range": "2023-01-01 to 2023-01-01"
        }
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'weather/Dublin/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify weather data was processed
        assert mock_transformer.process_incremental_data.call_count == 1
        assert mock_transformer.process_incremental_data.call_args[0][0] == 'weather'


def test_openmeteo_uses_location_specific_prefix():
    """Test that Open-Meteo uses location-specific prefix"""
    event = {
        "source": "custom.openmeteo",
        "detail": {
            "data_type": "openmeteo",
            "location": "Galway",
            "date_range": "2023-01-01 to 2023-01-01"
        }
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'weather/Galway/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify the correct prefix was used
        assert 'weather/Galway/' in mock_bronze_processor.list_timestamped_ingestion_objects.call_args[0][2]


def test_partial_failure_returns_unsuccessful_response():
    """Test that partial failure returns an unsuccessful response"""
    event = {
        "source": "custom.eirgrid",
        "detail": {
            "data_type": "eirgrid",
            "date_range": "2023-01-01 to 2023-01-01"
        }
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks - simulate partial failure
        mock_transformer.process_incremental_data.side_effect = [True, False]  # One success, one failure
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'demand/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify it returns failure response
        assert result['statusCode'] == 500
        assert 'partial_failure' in result['body']


def test_missing_bronze_data_does_not_report_success():
    """Test that missing Bronze data does not report success"""
    event = {
        "source": "custom.eirgrid",
        "detail": {
            "data_type": "eirgrid",
            "date_range": "2023-01-01 to 2023-01-01"
        }
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks - no bronze data found
        mock_transformer.process_incremental_data.return_value = False  # Simulate processing failure
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = []  # No files found
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify it reports failure
        assert result['statusCode'] == 500
        assert 'failed' in result['body']


def test_existing_gold_data_handled_idempotently():
    """Test that existing Gold data is handled idempotently"""
    event = {
        "source": "custom.eirgrid",
        "detail": {
            "data_type": "eirgrid",
            "date_range": "2023-01-01 to 2023-01-01"
        }
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True  # Should succeed
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'demand/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify success response
        assert result['statusCode'] == 200
        assert 'success' in result['body']


def test_direct_invocation_still_supported():
    """Test that direct invocation remains supported"""
    event = {
        "data_type": "demand",
        "date_str": "2023-01-01",
        "raw_data": {"test": "data"}
    }
    
    with patch('src.transformation.handler._data_transformer') as mock_transformer:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True
        
        # Call handler
        result = lambda_handler(event, Mock())
        
        # Verify direct invocation still works
        assert result['statusCode'] == 200
        assert 'success' in result['body']


def test_invalid_date_ranges_return_error():
    """Test that invalid date ranges return an appropriate error"""
    event = {
        "source": "custom.eirgrid",
        "detail": {
            "data_type": "eirgrid"
            # Missing date_range
        }
    }
    
    # Call handler
    result = lambda_handler(event, Mock())
    
    # Verify error response
    assert result['statusCode'] == 500
    assert 'error' in result['body']


def test_process_eirgrid_data():
    """Test the helper function process_eirgrid_data directly"""
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'demand/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call helper function
        success_results = process_eirgrid_data(
            {"data_type": "eirgrid"}, 
            "demand", 
            "2023-01-01", 
            "2023-01-01"
        )
        
        # Verify it returns successful results
        assert len(success_results) == 1
        assert success_results[0] is True


def test_process_openmeteo_data():
    """Test the helper function process_openmeteo_data directly"""
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks
        mock_transformer.process_incremental_data.return_value = True
        
        mock_bronze_processor.list_timestamped_ingestion_objects.return_value = [
            {'Key': 'weather/Dublin/2023-01-01/some_file.json', 'LastModified': '2023-01-01T00:00:00Z'}
        ]
        mock_bronze_processor.retrieve_bronze_data.return_value = {'test': 'data'}
        
        # Call helper function
        success_results = process_openmeteo_data(
            {"data_type": "openmeteo", "location": "Dublin"}, 
            "Dublin", 
            "2023-01-01", 
            "2023-01-01"
        )
        
        # Verify it returns successful results
        assert len(success_results) == 1
        assert success_results[0] is True


def test_aws_service_error_propagated():
    """Test that AWS service errors are propagated, not masked"""
    from botocore.exceptions import ClientError
    
    event = {
        "source": "custom.eirgrid",
        "detail": {
            "data_type": "eirgrid",
            "date_range": "2023-01-01 to 2023-01-01"
        }
    }
    
    # Import and patch the classes to use mocked instances
    with patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze_processor:
        
        # Setup mocks to raise an AWS service error
        mock_bronze_processor.list_timestamped_ingestion_objects.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'ListObjectsV2'
        )
        
        # Call handler and expect it to raise the error
        with pytest.raises(ClientError) as exc_info:
            lambda_handler(event, Mock())
        
        # Verify it's the right error
        assert exc_info.value.response['Error']['Code'] == 'AccessDenied'


def test_nonexistent_s3_object_returns_false():
    """Test that non-existent S3 objects return False in data quality metrics"""
    from botocore.exceptions import ClientError
    
    with patch('src.transformation.data_transformation.boto3.client') as mock_boto3_client:
        # Setup mock to raise NoSuchKey error
        mock_s3_client = Mock()
        mock_s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Not Found'}},
            'HeadObject'
        )
        mock_boto3_client.return_value = mock_s3_client
        
        # Create transformer instance
        from src.transformation.data_transformation import DataTransformer
        transformer = DataTransformer()
        transformer.config.BRONZE_BUCKET = "test-bronze-bucket"
        transformer.config.SILVER_BUCKET = "test-silver-bucket"
        transformer.config.GOLD_BUCKET = "test-gold-bucket"
        
        # Test data quality metrics
        metrics = transformer.get_data_quality_metrics('demand', '2023-01-01')
        
        # Verify it returns False for missing objects
        assert metrics['bronze_processed'] is False
        assert metrics['silver_processed'] is False
        assert metrics['gold_processed'] is False