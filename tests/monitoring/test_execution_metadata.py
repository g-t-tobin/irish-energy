"""
Tests for transformation execution monitoring metadata.
"""

from unittest.mock import Mock, patch

import pytest

from src.monitoring.service import MonitoringService
from src.transformation.handler import lambda_handler


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
def monitoring_service():
    service = MonitoringService.__new__(MonitoringService)
    service.storage = InMemoryMonitoringStorage()
    return service


def _invoke_handler(
    event, monitoring_service, transformer_result=True, bronze_files=None
):
    if bronze_files is None:
        bronze_files = [
            {
                'Key': 'weather/dublin/2026-11-04/raw.json',
                'LastModified': '2026-11-05T00:00:00Z'
            }
        ]

    with patch('src.transformation.handler._monitoring_service', monitoring_service), \
         patch('src.transformation.handler._data_transformer') as mock_transformer, \
         patch('src.transformation.handler._bronze_layer_processor') as mock_bronze:

        mock_transformer.process_incremental_data.return_value = transformer_result
        mock_bronze.list_timestamped_ingestion_objects.return_value = bronze_files
        mock_bronze.retrieve_bronze_data.return_value = {
            'date': '2026-11-04',
            'weather': []
        }

        return lambda_handler(event, Mock())


def _single_summary(monitoring_service):
    assert len(monitoring_service.storage.summaries) == 1
    return next(iter(monitoring_service.storage.summaries.values()))


def test_successful_openmeteo_records_actual_metadata(monitoring_service):
    event = {
        'source': 'irish-energy.ingestion',
        'detail-type': 'OpenMeteo Ingestion Complete',
        'detail': {
            'data_type': 'openmeteo',
            'location': 'dublin',
            'date_range': '2026-11-04 to 2026-11-04'
        }
    }

    result = _invoke_handler(event, monitoring_service)

    assert result['statusCode'] == 200
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'openmeteo'
    assert summary['date'] == '2026-11-04'
    assert summary['status'] == 'completed'
    assert summary['error_message'] is None
    assert summary['execution_id']
    assert summary['start_time']
    assert summary['end_time']


def test_failed_openmeteo_retains_actual_metadata(monitoring_service):
    event = {
        'source': 'irish-energy.ingestion',
        'detail-type': 'OpenMeteo Ingestion Complete',
        'detail': {
            'data_type': 'openmeteo',
            'location': 'dublin',
            'date_range': '2026-11-04 to 2026-11-04'
        }
    }

    result = _invoke_handler(event, monitoring_service, transformer_result=False)

    assert result['statusCode'] == 500
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'openmeteo'
    assert summary['date'] == '2026-11-04'
    assert summary['status'] == 'failed'
    assert summary['error_message'] == 'Some Open-Meteo data processing failed'


def test_successful_eirgrid_records_date_range(monitoring_service):
    event = {
        'source': 'irish-energy.ingestion',
        'detail-type': 'EirGrid Ingestion Complete',
        'detail': {
            'data_type': 'eirgrid',
            'date_range': '2026-11-04 to 2026-11-06'
        }
    }

    result = _invoke_handler(event, monitoring_service)

    assert result['statusCode'] == 200
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'eirgrid'
    assert summary['date'] == '2026-11-04 to 2026-11-06'
    assert summary['status'] == 'completed'
    assert summary['error_message'] is None


def test_failed_eirgrid_retains_date_range(monitoring_service):
    event = {
        'source': 'irish-energy.ingestion',
        'detail-type': 'EirGrid Ingestion Complete',
        'detail': {
            'data_type': 'eirgrid',
            'date_range': '2026-11-04 to 2026-11-05'
        }
    }

    result = _invoke_handler(event, monitoring_service, bronze_files=[])

    assert result['statusCode'] == 500
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'eirgrid'
    assert summary['date'] == '2026-11-04 to 2026-11-05'
    assert summary['status'] == 'failed'
    assert summary['error_message']


@pytest.mark.parametrize('detail', [
    {
        'data_type': 'openmeteo',
        'location': 'dublin'
    },
    {
        'data_type': 'openmeteo',
        'location': 'dublin',
        'date_range': 'not-a-valid-range'
    }
])
def test_malformed_event_metadata_is_handled_safely(monitoring_service, detail):
    event = {
        'source': 'irish-energy.ingestion',
        'detail-type': 'OpenMeteo Ingestion Complete',
        'detail': detail
    }

    result = _invoke_handler(event, monitoring_service)

    assert result['statusCode'] == 500
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'openmeteo'
    assert summary['date'] == 'unknown'
    assert summary['status'] == 'failed'
    assert summary['error_message']


def test_missing_event_metadata_is_handled_safely(monitoring_service):
    result = _invoke_handler({}, monitoring_service)

    assert result['statusCode'] == 500
    summary = _single_summary(monitoring_service)
    assert summary['data_type'] == 'transformation_pipeline'
    assert summary['date'] == 'unknown'
    assert summary['status'] == 'failed'
    assert summary['error_message']


def test_failure_without_metadata_preserves_existing_summary(monitoring_service):
    execution_id = monitoring_service.record_execution_start(
        'transformation_pipeline', 'unknown', 'pipeline'
    )

    monitoring_service.record_execution_failure(execution_id, 'boom')

    summary = monitoring_service.storage.summaries[execution_id]
    assert summary['data_type'] == 'transformation_pipeline'
    assert summary['date'] == 'unknown'
    assert summary['status'] == 'failed'
    assert summary['error_message'] == 'boom'
    assert summary['start_time']
    assert summary['end_time']
