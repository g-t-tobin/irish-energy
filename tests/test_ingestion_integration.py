"""
Integration tests for EirGrid and Open-Meteo ingestion with Bronze storage
"""

import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.ingestion.eirgrid_ingestion import EirGridIngestionClient
from src.ingestion.openmeteo_ingestion import OpenMeteoIngestionClient
from src.ingestion.orchestration import IngestionOrchestrator, create_local_ingestion_orchestrator
from src.storage.bronze_storage import LocalBronzeStorage
from src.common.config import Config


class TestEirGridIngestion:

    def test_fetch_demand_data_success(self):
        """Test successful demand data fetching"""
        config = Config()
        client = EirGridIngestionClient(config)

        # Mock successful response
        with patch.object(client.session, 'get') as mock_get:
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

            result = client.fetch_demand_data("2023-01-01")
            assert result is not None
            assert 'Rows' in result

    def test_fetch_demand_data_failure(self):
        """Test demand data fetching failure"""
        config = Config()
        client = EirGridIngestionClient(config)

        # Mock HTTP error
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = client.fetch_demand_data("2023-01-01")
            assert result is None


class TestOpenMeteoIngestion:

    def test_fetch_weather_data_success(self):
        """Test successful weather data fetching"""
        config = Config()
        client = OpenMeteoIngestionClient(config)

        # Mock successful response
        with patch.object(client.session, 'get') as mock_get:
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

            result = client.fetch_weather_data(53.3498, -6.2603, "2023-01-01", "2023-01-01")
            assert result is not None
            assert 'latitude' in result


class TestIngestionOrchestratorIntegration:

    def test_create_local_ingestion_orchestrator(self):
        """Test creating local ingestion orchestrator"""
        orchestrator = create_local_ingestion_orchestrator()
        assert orchestrator is not None
        assert isinstance(orchestrator.storage, LocalBronzeStorage)

    def test_ingest_single_day(self):
        """Test ingestion of single day data"""
        # Create orchestrator with mocked storage
        config = Config()
        storage = LocalBronzeStorage("./test_storage")

        # Mock the clients to avoid real API calls
        with patch('src.ingestion.eirgrid_ingestion.EirGridIngestionClient') as mock_eirgrid, \
             patch('src.ingestion.openmeteo_ingestion.OpenMeteoIngestionClient') as mock_openmeteo:

            # Setup mocks
            mock_eirgrid_instance = Mock()
            mock_openmeteo_instance = Mock()
            mock_eirgrid.return_value = mock_eirgrid_instance
            mock_openmeteo.return_value = mock_openmeteo_instance

            # Mock successful responses
            mock_eirgrid_instance.fetch_demand_data.return_value = {
                'test': 'demand_data'
            }
            mock_eirgrid_instance.fetch_generation_data.return_value = {
                'test': 'generation_data'
            }
            mock_openmeteo_instance.fetch_weather_data.return_value = {
                'test': 'weather_data'
            }

            # Mock storage success
            mock_eirgrid_instance.store_raw_data.return_value = True
            mock_openmeteo_instance.store_raw_data.return_value = True

            orchestrator = IngestionOrchestrator(config, storage)

            # Test ingestion
            result = orchestrator.ingest_single_day("2023-01-01", ["dublin"])

            assert 'date' in result
            assert 'stats' in result
            assert result['date'] == '2023-01-01'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])