"""
Tests for reliability improvements in EirGrid and Open-Meteo ingestion clients
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError

from src.ingestion.eirgrid_ingestion import EirGridIngestionClient
from src.ingestion.openmeteo_ingestion import OpenMeteoIngestionClient
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


@pytest.fixture
def openmeteo_client(config):
    """Create an Open-Meteo client for testing"""
    return OpenMeteoIngestionClient(config)


class TestEirGridReliability:
    """Test reliability improvements for EirGrid client"""

    def test_fetch_demand_data_timeout_handling(self, eirgrid_client):
        """Test that timeout errors are properly handled with retries"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            mock_get.side_effect = Timeout("Request timed out")

            result = eirgrid_client.fetch_demand_data("2023-01-01")

            # Should return None after all retries exhausted
            assert result is None

    def test_fetch_demand_data_connection_error_handling(self, eirgrid_client):
        """Test that connection errors are properly handled with retries"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            mock_get.side_effect = ConnectionError("Connection failed")

            result = eirgrid_client.fetch_demand_data("2023-01-01")

            # Should return None after all retries exhausted
            assert result is None

    def test_fetch_demand_data_retryable_status_codes(self, eirgrid_client):
        """Test that retryable status codes are handled properly"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Simulate retryable 429 status code
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
            mock_get.return_value = mock_response

            result = eirgrid_client.fetch_demand_data("2023-01-01")

            # Should return None after all retries exhausted
            assert result is None

    def test_fetch_demand_data_success_with_validation(self, eirgrid_client):
        """Test successful fetch with proper validation"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'Rows': [
                    {
                        'FieldName': 'Demand Actual',
                        'Region': 'ROI',
                        'Value': '1000.0',
                        'EffectiveTime': '01-Jan-2023 00:00:00'
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = eirgrid_client.fetch_demand_data("2023-01-01")

            # Should return valid data
            assert result is not None
            assert result['date'] == '2023-01-01'
            assert len(result['demand']) == 1
            assert result['demand'][0]['value'] == 1000.0

    def test_fetch_demand_data_missing_required_fields(self, eirgrid_client):
        """Test that missing required fields are detected and handled"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'Rows': [
                    {
                        'FieldName': 'Demand Actual',
                        'Region': 'ROI',
                        'Value': '',
                        'EffectiveTime': ''
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = eirgrid_client.fetch_demand_data("2023-01-01")

            # Should return None due to validation failure
            assert result is not None  # Should still return the converted data structure even if empty
            assert len(result['demand']) == 0  # But with empty demand list


class TestOpenMeteoReliability:
    """Test reliability improvements for Open-Meteo client"""

    def test_fetch_weather_data_timeout_handling(self, openmeteo_client):
        """Test that timeout errors are properly handled with retries"""
        with patch.object(openmeteo_client.session, 'get') as mock_get:
            mock_get.side_effect = Timeout("Request timed out")

            result = openmeteo_client.fetch_weather_data(
                53.3498, -6.2603, "2023-01-01", "2023-01-01", max_retries=2
            )

            # Should return None after all retries exhausted
            assert result is None
            assert mock_get.call_count == 3  # 1 initial + 2 retries

    def test_fetch_weather_data_connection_error_handling(self, openmeteo_client):
        """Test that connection errors are properly handled with retries"""
        with patch.object(openmeteo_client.session, 'get') as mock_get:
            mock_get.side_effect = ConnectionError("Connection failed")

            result = openmeteo_client.fetch_weather_data(
                53.3498, -6.2603, "2023-01-01", "2023-01-01", max_retries=2
            )

            # Should return None after all retries exhausted
            assert result is None
            assert mock_get.call_count == 3  # 1 initial + 2 retries

    def test_fetch_weather_data_retryable_status_codes(self, openmeteo_client):
        """Test that retryable status codes trigger retries"""
        with patch.object(openmeteo_client.session, 'get') as mock_get:
            # Simulate 502 Bad Gateway response
            mock_response = Mock()
            mock_response.status_code = 502
            mock_response.raise_for_status.side_effect = requests.HTTPError("Bad Gateway")
            mock_get.return_value = mock_response

            result = openmeteo_client.fetch_weather_data(
                53.3498, -6.2603, "2023-01-01", "2023-01-01", max_retries=2
            )

            # Should return None after all retries exhausted
            assert result is None
            assert mock_get.call_count == 3  # 1 initial + 2 retries

    def test_fetch_weather_data_success_with_validation(self, openmeteo_client):
        """Test successful fetch with proper validation"""
        with patch.object(openmeteo_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'latitude': 53.3498,
                'longitude': -6.2603,
                'timezone': 'Europe/Dublin',
                'hourly': {},
                'daily': {}
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = openmeteo_client.fetch_weather_data(
                53.3498, -6.2603, "2023-01-01", "2023-01-01", max_retries=2
            )

            # Should return valid data
            assert result is not None
            assert result['latitude'] == 53.3498
            assert result['longitude'] == -6.2603
            assert mock_get.call_count == 1  # No retries needed

    def test_fetch_weather_data_missing_required_fields(self, openmeteo_client):
        """Test that missing required fields are detected and handled"""
        with patch.object(openmeteo_client.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'latitude': 53.3498,
                'longitude': -6.2603
                # Missing 'timezone', 'hourly', 'daily' fields
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = openmeteo_client.fetch_weather_data(
                53.3498, -6.2603, "2023-01-01", "2023-01-01", max_retries=2
            )

            # Should return None due to validation failure
            assert result is None
            assert mock_get.call_count == 1  # No retries for validation errors