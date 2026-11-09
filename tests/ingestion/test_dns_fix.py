"""
Tests for DNS resolution fixes in EirGrid ingestion client
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError

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


class TestEirGridDNSFix:
    """Test DNS resolution fixes for EirGrid client"""

    def test_fetch_demand_data_dns_resolution_error_handling(self, eirgrid_client):
        """Test that DNS resolution errors are properly handled with retries"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Simulate DNS resolution error (this is what happens in VPC without internet)
            mock_get.side_effect = ConnectionError("Name or service not known")

            result = eirgrid_client.fetch_demand_data("2023-01-01")

            # Should return None after all retries exhausted
            assert result is None

    def test_fetch_generation_data_dns_resolution_error_handling(self, eirgrid_client):
        """Test that DNS resolution errors are properly handled for generation data"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            # Simulate DNS resolution error (this is what happens in VPC without internet)
            mock_get.side_effect = ConnectionError("Name or service not known")

            result = eirgrid_client.fetch_generation_data("2023-01-01")

            # Should return None after all retries exhausted
            assert result is None

    def test_fetch_demand_data_connection_error_handling(self, eirgrid_client):
        """Test that other connection errors are handled properly"""
        with patch.object(eirgrid_client.session, 'get') as mock_get:
            mock_get.side_effect = ConnectionError("Connection failed")

            result = eirgrid_client.fetch_demand_data("2023-01-01")

            # Should return None after all retries exhausted
            assert result is None