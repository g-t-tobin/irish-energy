"""
Comprehensive test to validate the EirGrid ingestion fixes
"""

import pytest
from unittest.mock import Mock, patch
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


class TestEirGridIngestionFixes:
    """Test that the EirGrid ingestion fixes work correctly"""

    def test_ingest_single_day_returns_false_on_dns_failure(self, eirgrid_client):
        """Test that ingest_single_day returns False when DNS fails"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Simulate DNS resolution error (VPC without internet)
            mock_get.side_effect = Exception("Name or service not known")

            # Test demand data fetching
            result = eirgrid_client.ingest_single_day("2023-01-01")
            assert result is False

    def test_ingest_single_day_returns_false_on_connection_failure(self, eirgrid_client):
        """Test that ingest_single_day returns False when connection fails"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Simulate connection error
            mock_get.side_effect = Exception("Connection failed")

            # Test demand data fetching
            result = eirgrid_client.ingest_single_day("2023-01-01")
            assert result is False

    def test_ingest_single_day_handles_both_demand_and_generation_failures(self, eirgrid_client):
        """Test that ingest_single_day returns False when either demand or generation fails"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Both demand and generation will fail
            mock_get.side_effect = Exception("Connection failed")

            # Test that both data types fail
            result = eirgrid_client.ingest_single_day("2023-01-01")
            assert result is False

    def test_ingest_single_day_handles_successful_case(self, eirgrid_client):
        """Test that ingest_single_day returns True when both data types succeed"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Mock successful responses for both demand and generation with proper Rows structure
            # This matches the actual EirGrid API response format expected by the converter
            mock_demand_response = Mock()
            mock_demand_response.status_code = 200
            mock_demand_response.json.return_value = {
                'Rows': [
                    {
                        'FieldName': 'Demand Actual',
                        'Region': 'ROI',
                        'Value': '1000.0',
                        'EffectiveTime': '01-Jan-2023 00:00:00'
                    }
                ]
            }
            mock_demand_response.raise_for_status.return_value = None

            mock_generation_response = Mock()
            mock_generation_response.status_code = 200
            mock_generation_response.json.return_value = {
                'Rows': [
                    {
                        'FieldName': 'Generation Actual',
                        'Region': 'ROI',
                        'Value': '2000.0',
                        'EffectiveTime': '01-Jan-2023 00:00:00'
                    }
                ]
            }
            mock_generation_response.raise_for_status.return_value = None

            # Set up the mock to return different responses for different calls
            mock_get.side_effect = [mock_demand_response, mock_generation_response]

            # Mock successful storage
            with patch.object(eirgrid_client, 'store_raw_data', return_value=True):
                result = eirgrid_client.ingest_single_day("2023-01-01")
                assert result is True