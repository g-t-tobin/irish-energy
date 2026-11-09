"""
Tests for corrected EirGrid ingestion behavior
"""
import pytest
from unittest.mock import Mock, patch
import json
import requests
from src.ingestion.eirgrid_ingestion import EirGridIngestionClient
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


class TestEirGridIngestionCorrections:
    """Test the corrected EirGrid ingestion behavior"""

    def test_ingest_single_day_both_sources_empty(self, eirgrid_client):
        """Test that empty data from both sources results in failed ingestion"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Mock empty data from both sources (successful API calls but empty data)
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'date': '2026-11-04',
                'demand': [],  # Empty demand data
                'generation': []  # Empty generation data
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock that we get the empty data back from converters
            with patch.object(eirgrid_client, '_convert_demand_response', return_value={'date': '2026-11-04', 'demand': []}) as mock_demand_convert, \
                 patch.object(eirgrid_client, '_convert_generation_response', return_value={'date': '2026-11-04', 'generation': []}) as mock_gen_convert:

                result = eirgrid_client.ingest_single_day("2026-11-04")
                # Should return False because neither source had valid data (empty lists)
                assert result is False

    def test_ingest_single_day_both_sources_have_data(self, eirgrid_client):
        """Test that valid data from both sources results in successful ingestion"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Mock valid data from both sources (actual EirGrid API response structure)
            # For demand
            mock_demand_response = Mock()
            mock_demand_response.status_code = 200
            mock_demand_response.json.return_value = {
                'Rows': [
                    {
                        'FieldName': 'Demand Actual',
                        'Region': 'ROI',
                        'Value': '1000.0',
                        'EffectiveTime': '04-Nov-2026 00:00:00'
                    }
                ]
            }
            mock_demand_response.raise_for_status.return_value = None

            # For generation
            mock_generation_response = Mock()
            mock_generation_response.status_code = 200
            mock_generation_response.json.return_value = {
                'Rows': [
                    {
                        'FieldName': 'Generation Actual',
                        'Region': 'ROI',
                        'Value': '2000.0',
                        'EffectiveTime': '04-Nov-2026 00:00:00'
                    }
                ]
            }
            mock_generation_response.raise_for_status.return_value = None

            # Set up the mock to return different responses for different calls
            mock_get.side_effect = [mock_demand_response, mock_generation_response]

            # Mock successful storage for both
            with patch.object(eirgrid_client, 'store_raw_data', return_value=True):
                result = eirgrid_client.ingest_single_day("2026-11-04")
                # Should return True because both sources had valid data
                assert result is True

    def test_ingest_date_range_statistics(self, eirgrid_client):
        """Test that ingest_date_range returns detailed statistics"""
        with patch.object(eirgrid_client, 'ingest_single_day') as mock_ingest:
            # Mock single day results
            mock_ingest.side_effect = [True, False, True]  # 2 successes, 1 failure

            stats = eirgrid_client.ingest_date_range("2026-11-04", "2026-11-06")

            # Check that we get detailed statistics
            assert stats['total_days'] == 3
            assert stats['successful_days'] == 2
            assert stats['failed_days'] == 1

class TestEirGridDiagnosticInstrumentation:
    """Test diagnostic instrumentation for EirGrid API responses"""

    def test_diagnostic_demand_many_valid_rows(self, eirgrid_client):
        """Test diagnostic instrumentation with many valid demand rows"""
        # Mock data with many valid demand rows
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1500.0',
                    'EffectiveTime': '06-Nov-2026 01:00:00'
                },
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '2000.0',
                    'EffectiveTime': '06-Nov-2026 02:00:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            # Capture log output
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got the expected result
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 3

                # Verify that diagnostic logging occurred
                # Note: We're just checking that the diagnostic method was called
                # The actual logging assertions would be complex to test reliably
                assert mock_logger.info.called

    def test_diagnostic_generation_many_valid_rows(self, eirgrid_client):
        """Test diagnostic instrumentation with many valid generation rows"""
        # Mock data with many valid generation rows
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Generation Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Generation Actual',
                    'Region': 'ROI',
                    'Value': '1500.0',
                    'EffectiveTime': '06-Nov-2026 01:00-00'
                },
                {
                    'FieldName': 'Generation Actual',
                    'Region': 'ROI',
                    'Value': '2000.0',
                    'EffectiveTime': '06-Nov-2026 02:00:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            # Capture log output
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_generation_data('2026-11-06')

                # Verify we got the expected result
                assert result is not None
                assert 'generation' in result
                assert len(result['generation']) == 3

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

    def test_diagnostic_rows_rejected_field_name_mismatch(self, eirgrid_client):
        """Test diagnostic instrumentation with rows rejected due to field name mismatch"""
        # Mock data with rows that won't match (no "DEMAND" in field name)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Wrong Field',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Generation Actual',  # This is a generation field
                    'Region': 'ROI',
                    'Value': '1500.0',
                    'EffectiveTime': '06-Nov-2026 01:00:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got empty result (because none match demand criteria)
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 0

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

    def test_diagnostic_rows_rejected_region_mismatch(self, eirgrid_client):
        """Test diagnostic instrumentation with rows rejected due to region mismatch"""
        # Mock data with rows that won't match due to region
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'IRELAND',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'EUROPE',
                    'Value': '1500.0',
                    'EffectiveTime': '06-Nov-2026 01:00:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got empty result
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 0

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

    def test_diagnostic_empty_rows(self, eirgrid_client):
        """Test diagnostic instrumentation with empty Rows"""
        # Mock data with empty Rows
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': []
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got empty result
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 0

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

    def test_diagnostic_missing_rows(self, eirgrid_client):
        """Test diagnostic instrumentation with missing Rows field"""
        # Mock data with missing Rows
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'OtherKey': 'SomeValue'
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got empty result
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 0

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

    def test_diagnostic_malformed_rows(self, eirgrid_client):
        """Test diagnostic instrumentation with malformed row entries"""
        # Mock data with malformed rows
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                'Not a dict',
                123,
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got one valid result
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 1

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

    def test_diagnostic_invalid_numeric_values(self, eirgrid_client):
        """Test diagnostic instrumentation with invalid numeric values"""
        # Mock data with invalid numeric values
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': 'invalid',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 01:00:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got one valid result (the second one)
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 1

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

    def test_diagnostic_duplicate_timestamps(self, eirgrid_client):
        """Test diagnostic instrumentation with duplicate timestamps"""
        # Mock data with duplicate timestamps
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1500.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'  # Duplicate timestamp
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to return our mock
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response):
            with patch('src.ingestion.eirgrid_ingestion.logger') as mock_logger:
                result = eirgrid_client.fetch_demand_data('2026-11-06')

                # Verify we got both results
                assert result is not None
                assert 'demand' in result
                assert len(result['demand']) == 2

                # Verify that diagnostic logging occurred
                assert mock_logger.info.called

class TestEirGridDateRangeHandling:
    """Test date range handling for full day data retrieval"""

    def test_demand_date_range_parameters(self, eirgrid_client):
        """Test that demand data requests use correct date range parameters"""
        # Mock data with multiple rows to verify date range works
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1500.0',
                    'EffectiveTime': '06-Nov-2026 00:15:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to capture the actual request parameters
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response) as mock_get:
            result = eirgrid_client.fetch_demand_data('2026-11-06')

            # Verify we got results
            assert result is not None
            assert 'demand' in result
            assert len(result['demand']) == 2

            # Verify the request was made with correct date range parameters
            call_args = mock_get.call_args
            params = call_args[1]['params']  # Get the params from the call

            # Check that date range covers full day
            assert params['datefrom'] == '06-Nov-2026 00:00'
            assert params['dateto'] == '07-Nov-2026 00:00'

    def test_generation_date_range_parameters(self, eirgrid_client):
        """Test that generation data requests use correct date range parameters"""
        # Mock data with multiple rows to verify date range works
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Generation Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '06-Nov-2026 00:00:00'
                },
                {
                    'FieldName': 'Generation Actual',
                    'Region': 'ROI',
                    'Value': '1500.0',
                    'EffectiveTime': '06-Nov-2026 00:15:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to capture the actual request parameters
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response) as mock_get:
            result = eirgrid_client.fetch_generation_data('2026-11-06')

            # Verify we got results
            assert result is not None
            assert 'generation' in result
            assert len(result['generation']) == 2

            # Verify the request was made with correct date range parameters
            call_args = mock_get.call_args
            params = call_args[1]['params']  # Get the params from the call

            # Check that date range covers full day
            assert params['datefrom'] == '06-Nov-2026 00:00'
            assert params['dateto'] == '07-Nov-2026 00:00'

    def test_date_range_boundary_edge_cases(self, eirgrid_client):
        """Test date range calculation with different date inputs"""
        # Test with a date that has day=1 to ensure day rollover works correctly
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Rows': [
                {
                    'FieldName': 'Demand Actual',
                    'Region': 'ROI',
                    'Value': '1000.0',
                    'EffectiveTime': '01-Jan-2026 00:00:00'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None

        # Patch the session to capture the actual request parameters
        with patch.object(eirgrid_client.session, 'get', return_value=mock_response) as mock_get:
            result = eirgrid_client.fetch_demand_data('2026-01-01')

            # Verify we got results
            assert result is not None

            # Verify the request was made with correct date range parameters
            call_args = mock_get.call_args
            params = call_args[1]['params']  # Get the params from the call

            # Check that date range covers full day
            assert params['datefrom'] == '01-Jan-2026 00:00'
            assert params['dateto'] == '02-Jan-2026 00:00'