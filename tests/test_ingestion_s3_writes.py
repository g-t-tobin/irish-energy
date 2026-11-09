"""
Tests for ingestion functionality and S3 writes
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import boto3

from src.ingestion.eirgrid_ingestion import EirGridIngestionClient
from src.ingestion.openmeteo_ingestion import OpenMeteoIngestionClient


class TestIngestionS3Writes:
    """Test that ingestion functions properly write to S3"""

    def test_eirgrid_store_raw_data_s3_write(self):
        """Test that EirGrid stores data to correct S3 bucket and key"""
        # Mock S3 client
        with patch('boto3.client') as mock_boto_client:
            mock_s3_client = Mock()
            mock_boto_client.return_value = mock_s3_client

            # Create client with mock
            client = EirGridIngestionClient()

            # Sample data
            sample_data = {
                'date': '2023-01-01',
                'demand_values': [
                    {'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}
                ]
            }

            # Test storing data
            success = client.store_raw_data(sample_data, 'demand', '2023-01-01', 'test-ingestion-123')

            # Verify S3 put_object was called with correct parameters
            assert success is True
            mock_s3_client.put_object.assert_called_once()

            # Get call arguments
            call_args = mock_s3_client.put_object.call_args
            kwargs = call_args.kwargs

            # Verify bucket and key
            assert kwargs['Bucket'] == client.config.BRONZE_BUCKET
            assert 'demand/2023-01-01/test-ingestion-123_raw.json' in kwargs['Key']

            # Verify metadata
            expected_metadata = {
                'source': 'EirGrid',
                'data_type': 'demand',
                'date': '2023-01-01',
                'timestamp': datetime.utcnow().isoformat(),  # This will vary, so we just check it exists
                'version': '1.0',
                'ingestion_status': 'success',
                'ingestion_id': 'test-ingestion-123'
            }
            assert 'Metadata' in kwargs
            assert kwargs['Metadata']['source'] == 'EirGrid'
            assert kwargs['Metadata']['data_type'] == 'demand'
            assert kwargs['Metadata']['date'] == '2023-01-01'
            assert kwargs['Metadata']['ingestion_id'] == 'test-ingestion-123'

    def test_openmeteo_store_weather_data_s3_write(self):
        """Test that Open-Meteo stores weather data to correct S3 bucket and key"""
        # Mock S3 client
        with patch('boto3.client') as mock_boto_client:
            mock_s3_client = Mock()
            mock_boto_client.return_value = mock_s3_client

            # Create client with mock
            client = OpenMeteoIngestionClient()

            # Sample weather data
            sample_data = {
                'latitude': 53.3498,
                'longitude': -6.2603,
                'hourly': {
                    'time': ['2023-01-01T00:00:00Z'],
                    'temperature_2m': [5.2]
                },
                'daily': {}
            }

            # Test storing data
            success = client.store_raw_data(sample_data, 'dublin', '2023-01-01', 'test-ingestion-456')

            # Verify S3 put_object was called with correct parameters
            assert success is True
            mock_s3_client.put_object.assert_called_once()

            # Get call arguments
            call_args = mock_s3_client.put_object.call_args
            kwargs = call_args.kwargs

            # Verify bucket and key (note: weather data goes in weather/{location}/{date}/ prefix)
            assert kwargs['Bucket'] == client.config.BRONZE_BUCKET
            assert 'weather/dublin/2023-01-01/test-ingestion-456_raw.json' in kwargs['Key']

            # Verify metadata has required fields
            assert 'Metadata' in kwargs
            assert kwargs['Metadata']['source'] == 'Open-Meteo'
            assert kwargs['Metadata']['location'] == 'dublin'
            assert kwargs['Metadata']['date'] == '2023-01-01'
            assert kwargs['Metadata']['ingestion_id'] == 'test-ingestion-456'

    def test_ingestion_returns_correct_stats(self):
        """Test that ingestion functions return proper stats"""
        # Mock S3 and API calls
        with patch('boto3.client') as mock_boto_client, \
             patch.object(EirGridIngestionClient, 'fetch_demand_data') as mock_fetch_demand, \
             patch.object(EirGridIngestionClient, 'fetch_generation_data') as mock_fetch_generation, \
             patch.object(EirGridIngestionClient, 'store_raw_data') as mock_store:

            mock_s3_client = Mock()
            mock_boto_client.return_value = mock_s3_client

            # Setup mocks
            mock_fetch_demand.return_value = {
                'date': '2023-01-01',
                'demand_values': [{'timestamp': '2023-01-01T00:00:00Z', 'value': 1000}]
            }
            mock_fetch_generation.return_value = {
                'date': '2023-01-01',
                'generation_values': [{'timestamp': '2023-01-01T00:00:00Z', 'value': 1500}]
            }
            mock_store.return_value = True

            # Create client
            client = EirGridIngestionClient()

            # Test ingestion
            stats = client.ingest_date_range('2023-01-01', '2023-01-01', 'test-ingestion-789')

            # Verify stats structure
            assert 'successful_days' in stats
            assert 'failed_days' in stats
            assert 'total_days' in stats
            assert stats['successful_days'] == 1
            assert stats['failed_days'] == 0
            assert stats['total_days'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])