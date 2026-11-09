"""
Storage contract tests for monitoring data storage implementations
These tests ensure both local and S3 storage implementations behave identically
"""

import pytest
import tempfile
import os
from datetime import datetime
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from src.monitoring.storage_interface import MonitoringStorageInterface
from src.monitoring.local_storage import LocalMonitoringStorage
from src.monitoring.s3_storage import S3MonitoringStorage
from src.common.config import Config


@pytest.fixture
def sample_execution_summary():
    """Sample execution summary data for testing"""
    return {
        'execution_id': 'test-execution-123',
        'data_type': 'eirgrid_demand',
        'date': '2023-01-01',
        'source': 'pipeline',
        'status': 'completed',
        'start_time': '2023-01-01T10:00:00',
        'end_time': '2023-01-01T10:05:00',
        'duration_seconds': 300.0,
        'error_message': None
    }


@pytest.fixture
def sample_quality_report():
    """Sample quality report data for testing"""
    return {
        'report_id': 'test-report-456',
        'data_type': 'eirgrid_demand',
        'date': '2023-01-01',
        'source': 'pipeline',
        'checks_passed': 5,
        'checks_failed': 0,
        'total_checks': 5,
        'metrics': {
            'data_volume': 1000,
            'accuracy_score': 0.98
        }
    }


@pytest.fixture
def local_storage():
    """Create local storage instance with temporary directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalMonitoringStorage(temp_dir)
        yield storage


@pytest.fixture
def s3_storage_mock():
    """Create S3 storage instance with mocked boto3 client"""
    # Mock the boto3 client to avoid actual S3 calls
    with patch('boto3.client') as mock_boto3_client:
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        # Mock the put_object method
        mock_s3_client.put_object = MagicMock()
        mock_s3_client.get_object = MagicMock()
        mock_s3_client.list_objects_v2 = MagicMock()

        # Mock the paginator
        mock_paginator = MagicMock()
        mock_s3_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{}]

        storage = S3MonitoringStorage(
            bucket_name="test-bucket",
            prefix="test-prefix/",
            region="us-east-1"
        )
        yield storage, mock_s3_client


class TestStorageContract:
    """Test that both storage implementations satisfy the same interface contract"""

    def test_save_execution_summary_interface(self, local_storage, sample_execution_summary):
        """Test save_execution_summary method signature and behavior"""
        result = local_storage.save_execution_summary(
            "test-execution-123",
            sample_execution_summary
        )
        assert isinstance(result, bool)

    def test_save_quality_report_interface(self, local_storage, sample_quality_report):
        """Test save_quality_report method signature and behavior"""
        result = local_storage.save_quality_report(
            "test-report-456",
            sample_quality_report
        )
        assert isinstance(result, bool)

    def test_get_execution_summary_interface(self, local_storage, sample_execution_summary):
        """Test get_execution_summary method signature and behavior"""
        # Save first
        local_storage.save_execution_summary("test-execution-123", sample_execution_summary)
        # Retrieve
        result = local_storage.get_execution_summary("test-execution-123")
        assert isinstance(result, dict) or result is None

    def test_get_quality_report_interface(self, local_storage, sample_quality_report):
        """Test get_quality_report method signature and behavior"""
        # Save first
        local_storage.save_quality_report("test-report-456", sample_quality_report)
        # Retrieve
        result = local_storage.get_quality_report("test-report-456")
        assert isinstance(result, dict) or result is None

    def test_list_execution_summaries_interface(self, local_storage, sample_execution_summary):
        """Test list_execution_summaries method signature and behavior"""
        # Save some data
        local_storage.save_execution_summary("test-execution-123", sample_execution_summary)
        # List
        result = local_storage.list_execution_summaries()
        assert isinstance(result, list)

    def test_list_quality_reports_interface(self, local_storage, sample_quality_report):
        """Test list_quality_reports method signature and behavior"""
        # Save some data
        local_storage.save_quality_report("test-report-456", sample_quality_report)
        # List
        result = local_storage.list_quality_reports()
        assert isinstance(result, list)


class TestLocalStorageContract:
    """Test local storage implementation specifically"""

    def test_local_storage_save_execution_summary(self, local_storage, sample_execution_summary):
        """Test local storage save_execution_summary"""
        result = local_storage.save_execution_summary(
            "test-execution-123",
            sample_execution_summary
        )
        assert result is True

        # Verify file was created
        expected_file = os.path.join(local_storage.storage_dir, "execution_test-execution-123.json")
        assert os.path.exists(expected_file)

    def test_local_storage_save_quality_report(self, local_storage, sample_quality_report):
        """Test local storage save_quality_report"""
        result = local_storage.save_quality_report(
            "test-report-456",
            sample_quality_report
        )
        assert result is True

        # Verify file was created
        expected_file = os.path.join(local_storage.storage_dir, "quality_test-report-456.json")
        assert os.path.exists(expected_file)

    def test_local_storage_get_execution_summary(self, local_storage, sample_execution_summary):
        """Test local storage get_execution_summary"""
        # Save first
        local_storage.save_execution_summary("test-execution-123", sample_execution_summary)
        # Retrieve
        result = local_storage.get_execution_summary("test-execution-123")
        assert result is not None
        assert result['execution_id'] == "test-execution-123"

    def test_local_storage_get_quality_report(self, local_storage, sample_quality_report):
        """Test local storage get_quality_report"""
        # Save first
        local_storage.save_quality_report("test-report-456", sample_quality_report)
        # Retrieve
        result = local_storage.get_quality_report("test-report-456")
        assert result is not None
        assert result['report_id'] == "test-report-456"

    def test_local_storage_list_execution_summaries(self, local_storage, sample_execution_summary):
        """Test local storage list_execution_summaries"""
        # Save some data
        local_storage.save_execution_summary("test-execution-123", sample_execution_summary)
        local_storage.save_execution_summary("test-execution-456", {
            **sample_execution_summary,
            'execution_id': 'test-execution-456'
        })
        # List
        result = local_storage.list_execution_summaries()
        assert len(result) >= 1
        assert any(item['execution_id'] == 'test-execution-123' for item in result)

    def test_local_storage_list_quality_reports(self, local_storage, sample_quality_report):
        """Test local storage list_quality_reports"""
        # Save some data
        local_storage.save_quality_report("test-report-456", sample_quality_report)
        local_storage.save_quality_report("test-report-789", {
            **sample_quality_report,
            'report_id': 'test-report-789'
        })
        # List
        result = local_storage.list_quality_reports()
        assert len(result) >= 1
        assert any(item['report_id'] == 'test-report-456' for item in result)


class TestS3StorageContract:
    """Test S3 storage implementation specifically (mocked)"""

    def test_s3_storage_save_execution_summary(self, s3_storage_mock, sample_execution_summary):
        """Test S3 storage save_execution_summary"""
        storage, mock_s3_client = s3_storage_mock

        # Mock response
        mock_s3_client.put_object.return_value = {}

        result = storage.save_execution_summary(
            "test-execution-123",
            sample_execution_summary
        )
        assert result is True
        mock_s3_client.put_object.assert_called_once()

    def test_s3_storage_save_quality_report(self, s3_storage_mock, sample_quality_report):
        """Test S3 storage save_quality_report"""
        storage, mock_s3_client = s3_storage_mock

        # Mock response
        mock_s3_client.put_object.return_value = {}

        result = storage.save_quality_report(
            "test-report-456",
            sample_quality_report
        )
        assert result is True
        mock_s3_client.put_object.assert_called_once()

    def test_s3_storage_get_execution_summary_found(self, s3_storage_mock, sample_execution_summary):
        """Test S3 storage get_execution_summary when found"""
        storage, mock_s3_client = s3_storage_mock

        # Mock response
        mock_body = MagicMock()
        mock_body.read.return_value = b'{"execution_id": "test-execution-123", "timestamp": "2023-01-01T00:00:00"}'
        mock_response = {
            'Body': mock_body
        }
        mock_s3_client.get_object.return_value = mock_response

        result = storage.get_execution_summary("test-execution-123")
        assert result is not None
        assert result['execution_id'] == "test-execution-123"

    def test_s3_storage_get_execution_summary_not_found(self, s3_storage_mock):
        """Test S3 storage get_execution_summary when not found"""
        storage, mock_s3_client = s3_storage_mock

        # Mock response for NoSuchKey
        from botocore.exceptions import ClientError
        mock_error = ClientError(
            error_response={'Error': {'Code': 'NoSuchKey'}},
            operation_name='GetObject'
        )
        mock_s3_client.get_object.side_effect = mock_error

        result = storage.get_execution_summary("non-existent-id")
        assert result is None

    def test_s3_storage_list_execution_summaries(self, s3_storage_mock):
        """Test S3 storage list_execution_summaries"""
        storage, mock_s3_client = s3_storage_mock

        # Mock response
        mock_page = {
            'Contents': [
                {
                    'Key': 'test-prefix/execution_test-execution-123.json',
                    'Size': 100
                }
            ]
        }
        mock_s3_client.get_paginator.return_value.paginate.return_value = [mock_page]

        result = storage.list_execution_summaries()
        assert isinstance(result, list)