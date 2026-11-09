"""
Tests for Open-Meteo execution monitoring metadata.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from src.common.config import Config
from src.ingestion.openmeteo_ingestion import OpenMeteoIngestionClient
from src.monitoring.service import MonitoringService


class InMemoryMonitoringStorage:
    """In-memory monitoring storage used to avoid AWS/local file access."""

    def __init__(self):
        self.summaries = {}

    def save_execution_summary(self, execution_id, summary):
        self.summaries[execution_id] = dict(summary)
        return True

    def get_execution_summary(self, execution_id):
        summary = self.summaries.get(execution_id)
        return dict(summary) if summary is not None else None


@pytest.fixture
def openmeteo_context():
    storage = InMemoryMonitoringStorage()
    monitoring_service = MonitoringService.__new__(MonitoringService)
    monitoring_service.storage = storage

    with patch('src.ingestion.openmeteo_ingestion.boto3.client'), \
         patch('src.ingestion.openmeteo_ingestion.MonitoringService',
               return_value=monitoring_service):
        client = OpenMeteoIngestionClient(Config())

    return client, monitoring_service


def _single_summary(monitoring_service):
    assert len(monitoring_service.storage.summaries) == 1
    return next(iter(monitoring_service.storage.summaries.values()))


def test_successful_fetch_records_actual_openmeteo_metadata(openmeteo_context):
    client, monitoring_service = openmeteo_context
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        'latitude': 53.3498,
        'longitude': -6.2603,
        'timezone': 'Europe/Dublin',
        'hourly': {'time': ['2026-11-04T00:00', '2026-11-04T01:00']},
        'daily': {}
    }
    response.raise_for_status.return_value = None

    with patch.object(client.session, 'get', return_value=response), \
         patch.object(client, '_rate_limit'):
        result = client.fetch_weather_data(
            53.3498, -6.2603, '2026-11-04', '2026-11-05', max_retries=0
        )

    assert result is not None
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'openmeteo'
    assert summary['date'] == '2026-11-04 to 2026-11-05'
    assert summary['status'] == 'completed'
    assert summary['source'] == 'Open-Meteo'
    assert summary['error_message'] is None


def test_failed_fetch_preserves_actual_openmeteo_metadata(openmeteo_context):
    client, monitoring_service = openmeteo_context

    with patch.object(client.session, 'get',
                      side_effect=requests.exceptions.Timeout('request timed out')), \
         patch.object(client, '_rate_limit'):
        result = client.fetch_weather_data(
            51.8985, -8.4756, '2026-10-21', '2026-10-21', max_retries=0
        )

    assert result is None
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'openmeteo'
    assert summary['date'] == '2026-10-21 to 2026-10-21'
    assert summary['status'] == 'failed'
    assert summary['source'] == 'Open-Meteo'
    assert 'Timeout' in summary['error_message']
