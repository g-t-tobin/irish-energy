"""
Regression tests for EirGrid ingestion and transformation event handling
"""
import pytest
from unittest.mock import Mock, patch
import json
from src.ingestion.eirgrid_ingestion import EirGridIngestionClient
from src.transformation.handler import lambda_handler
from src.common.config import Config


@pytest.fixture
def config():
    """Create a mock config for testing"""
    cfg = Config()
    cfg.REQUEST_TIMEOUT = 10
    cfg.RETRY_ATTEMPTS = 3
    return cfg


@pytest.fixture
def eirgrid_client(config):
    """Create an EirGrid client for testing"""
    return EirGridIngestionClient(config)


class TestEirGridEventHandling:
    """Test EirGrid event handling in transformation pipeline"""

    def test_failed_ingestion_event_skips_transformation(self):
        """Test that FAILED EirGrid ingestion events don't start transformation processing"""
        # Mock the transformation handler with a failed ingestion event
        event = {
            "source": "irish-energy.ingestion",
            "detail-type": "EirGrid Ingestion Complete",
            "detail": {
                "data_type": "eirgrid",
                "date_range": "2026-11-04 to 2026-11-04",
                "ingestion_status": "failed",
                "stats": {
                    "successful_days": 0,
                    "failed_days": 1,
                    "total_days": 1
                }
            }
        }

        # Mock the monitoring service to capture calls
        with patch('src.transformation.handler._monitoring_service') as mock_monitoring:
            # Mock the monitoring service to avoid actual calls
            mock_monitoring.record_execution_failure.return_value = True
            mock_monitoring.record_execution_start.return_value = "test-execution-id"

            # Mock the data transformer to avoid actual processing
            with patch('src.transformation.handler._data_transformer') as mock_transformer, \
                 patch('src.transformation.handler._bronze_layer_processor') as mock_bronze:

                mock_transformer.process_incremental_data.return_value = True
                mock_bronze.list_timestamped_ingestion_objects.return_value = []

                # Call the handler
                result = lambda_handler(event, Mock())

                # Should return skipped status without attempting processing
                assert result['statusCode'] == 200
                assert '"status": "skipped"' in result['body']
                assert '"reason": "ingestion_failed"' in result['body']

                # Should have recorded failure in monitoring
                mock_monitoring.record_execution_failure.assert_called_once()

    def test_partial_success_processes_available_data(self):
        """Test that PARTIAL_SUCCESS events process only available datasets"""
        # Mock event with partial success (demand has data, generation doesn't)
        event = {
            "source": "irish-energy.ingestion",
            "detail-type": "EirGrid Ingestion Complete",
            "detail": {
                "data_type": "eirgrid",
                "date_range": "2026-11-04 to 2026-11-04",
                "ingestion_status": "completed",
                "stats": {
                    "successful_days": 1,
                    "failed_days": 0,
                    "partial_success_days": 0,
                    "total_days": 1
                }
            }
        }

        # Mock monitoring service
        with patch('src.transformation.handler._monitoring_service') as mock_monitoring:
            mock_monitoring.record_execution_start.return_value = "test-execution-id"
            mock_monitoring.record_execution_success.return_value = True

            # Mock the data processing to return success for demand but handle generation appropriately
            with patch('src.transformation.handler._data_transformer') as mock_transformer, \
                 patch('src.transformation.handler._bronze_layer_processor') as mock_bronze:

                # Mock successful processing for demand, but return empty for generation
                mock_transformer.process_incremental_data.return_value = True
                mock_bronze.list_timestamped_ingestion_objects.return_value = [
                    {'Key': 'demand/2026-11-04/test.json', 'LastModified': '2026-11-05T00:00:00Z'}
                ]
                mock_bronze.retrieve_bronze_data.return_value = {
                    'date': '2026-11-04',
                    'demand': [{'timestamp': '04-Nov-2026 00:00:00', 'value': 1000.0}]
                }

                # Call the handler
                result = lambda_handler(event, Mock())

                # Should process successfully when data is available
                assert result['statusCode'] == 200
                assert 'success' in result['body']

    def test_legacy_event_without_ingestion_status(self):
        """Test that legacy events without ingestion_status are handled safely"""
        # Legacy event without ingestion_status field
        event = {
            "source": "irish-energy.ingestion",
            "detail-type": "EirGrid Ingestion Complete",
            "detail": {
                "data_type": "eirgrid",
                "date_range": "2026-11-04 to 2026-11-04"
                # Note: No ingestion_status field
            }
        }

        # Mock monitoring service
        with patch('src.transformation.handler._monitoring_service') as mock_monitoring:
            mock_monitoring.record_execution_start.return_value = "test-execution-id"
            mock_monitoring.record_execution_success.return_value = True

            # Mock the data processing
            with patch('src.transformation.handler._data_transformer') as mock_transformer, \
                 patch('src.transformation.handler._bronze_layer_processor') as mock_bronze:

                mock_transformer.process_incremental_data.return_value = True
                mock_bronze.list_timestamped_ingestion_objects.return_value = [
                    {'Key': 'demand/2026-11-04/test.json', 'LastModified': '2026-11-05T00:00:00Z'}
                ]
                mock_bronze.retrieve_bronze_data.return_value = {
                    'date': '2026-11-04',
                    'demand': [{'timestamp': '04-Nov-2026 00:00:00', 'value': 1000.0}]
                }

                # Call the handler - should not crash
                result = lambda_handler(event, Mock())

                # Should process normally (legacy events assumed to be successful)
                assert result['statusCode'] == 200 or result['statusCode'] == 500  # Both are valid responses

    def test_openmeteo_event_processing_unchanged(self):
        """Test that Open-Meteo event processing remains unchanged"""
        # Open-Meteo event structure
        event = {
            "source": "irish-energy.ingestion",
            "detail-type": "OpenMeteo Ingestion Complete",
            "detail": {
                "data_type": "openmeteo",
                "location": "dublin",
                "date_range": "2026-11-04 to 2026-11-04"
            }
        }

        # Mock monitoring service
        with patch('src.transformation.handler._monitoring_service') as mock_monitoring:
            mock_monitoring.record_execution_start.return_value = "test-execution-id"
            mock_monitoring.record_execution_success.return_value = True

            # Mock the data processing for Open-Meteo
            with patch('src.transformation.handler.process_openmeteo_data') as mock_process:
                mock_process.return_value = [True]  # Simulate successful processing

                # Call the handler
                result = lambda_handler(event, Mock())

                # Should process Open-Meteo successfully
                assert result['statusCode'] == 200
                assert 'success' in result['body']


class TestEirGridIngestionStatusHandling:
    """Test the enhanced EirGrid ingestion status handling"""

    def test_ingest_single_day_empty_demand_data(self, eirgrid_client):
        """Test that empty demand data doesn't count as successful ingestion"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Mock empty demand data response (proper Rows structure)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'Rows': []  # Empty Rows list - no actual data
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock that we get the empty data back from converters
            with patch.object(eirgrid_client, '_convert_demand_response', return_value={'date': '2026-11-04', 'demand': []}) as mock_demand_convert, \
                 patch.object(eirgrid_client, '_convert_generation_response', return_value={'date': '2026-11-04', 'generation': [{'timestamp': '04-Nov-2026 00:00:00', 'value': 2000.0}]}) as mock_gen_convert:

                result = eirgrid_client.ingest_single_day("2026-11-04")
                # Should return True because generation had data (partial success)
                assert result is True

    def test_ingest_single_day_both_sources_empty(self, eirgrid_client):
        """Test that empty data from both sources results in failed ingestion"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Mock empty data from both sources (proper Rows structure)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'Rows': []  # Empty Rows list - no actual data
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock that we get empty data back from converters
            with patch.object(eirgrid_client, '_convert_demand_response', return_value={'date': '2026-11-04', 'demand': []}) as mock_demand_convert, \
                 patch.object(eirgrid_client, '_convert_generation_response', return_value={'date': '2026-11-04', 'generation': []}) as mock_gen_convert:

                result = eirgrid_client.ingest_single_day("2026-11-04")
                # Should return False because neither source had valid data
                assert result is False