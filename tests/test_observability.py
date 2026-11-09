"""
Test file for the observability framework
"""
import pytest
from datetime import datetime
from src.observability.models import (
    PipelineExecutionMetrics, StageMetrics, DatasetMetrics, DatasetFreshnessMetrics,
    QualityMetrics, DataLineage, ExecutionStatus, StageStatus, FreshnessStatus, QualityStatus
)
from src.observability.collector import ObservabilityCollector
from src.observability.metrics import ObservabilityMetricsService
from src.observability.service import ObservabilityService
from src.monitoring.service import MonitoringService


def test_models_creation():
    """Test that observability models can be instantiated"""

    # Test PipelineExecutionMetrics
    pipeline_metrics = PipelineExecutionMetrics(
        execution_id="test-execution",
        pipeline_date="2023-01-01",
        start_timestamp=datetime.now(),
        end_timestamp=None,
        duration_seconds=300.0,
        execution_status=ExecutionStatus.RUNNING,
        stage_count=3,
        successful_stages=1,
        failed_stages=0,
        overall_result="running"
    )

    assert pipeline_metrics.execution_id == "test-execution"
    assert pipeline_metrics.pipeline_date == "2023-01-01"

    # Test StageMetrics
    stage_metrics = StageMetrics(
        execution_id="test-execution",
        stage_name="test-stage",
        start_timestamp=datetime.now(),
        end_timestamp=None,
        duration_seconds=60.0,
        stage_status=StageStatus.RUNNING,
        input_record_count=1000,
        output_record_count=950
    )

    assert stage_metrics.stage_name == "test-stage"
    assert stage_metrics.input_record_count == 1000

    # Test DatasetMetrics
    dataset_metrics = DatasetMetrics(
        dataset_name="test-dataset",
        data_layer="bronze",
        partition_date="2023-01-01",
        record_count=1000,
        file_count=5,
        total_file_size_bytes=1024000,
        latest_timestamp=datetime.now(),
        earliest_timestamp=datetime.now(),
        last_successful_processing=datetime.now()
    )

    assert dataset_metrics.dataset_name == "test-dataset"
    assert dataset_metrics.record_count == 1000

    # Test DatasetFreshnessMetrics
    freshness_metrics = DatasetFreshnessMetrics(
        dataset_name="test-dataset",
        expected_update_frequency="daily",
        last_successful_ingestion=datetime.now(),
        last_successful_transformation=datetime.now(),
        data_age_days=1.0,
        freshness_status=FreshnessStatus.FRESH,
        freshness_threshold_days=2,
        last_assessment_timestamp=datetime.now()
    )

    assert freshness_metrics.dataset_name == "test-dataset"
    assert freshness_metrics.freshness_status == FreshnessStatus.FRESH

    # Test QualityMetrics
    quality_metrics = QualityMetrics(
        dataset_name="test-dataset",
        data_layer="silver",
        pipeline_date="2023-01-01",
        assessment_timestamp=datetime.now(),
        total_records=1000,
        passed_checks=950,
        failed_checks=50,
        warning_checks=0,
        overall_score=0.95,
        quality_status=QualityStatus.PASS
    )

    assert quality_metrics.dataset_name == "test-dataset"
    assert quality_metrics.overall_score == 0.95

    # Test DataLineage
    lineage = DataLineage(
        dataset_name="test-dataset",
        data_layer="silver",
        partition_date="2023-01-01",
        source="ingestion",
        pipeline_execution_id="exec-123",
        processing_stage="transformation",
        input_dataset="bronze-dataset",
        output_dataset="silver-dataset",
        processing_timestamp=datetime.now(),
        quality_assessment_ref="qa-ref-123"
    )

    assert lineage.dataset_name == "test-dataset"
    assert lineage.source == "ingestion"


def test_collector_functions():
    """Test observability collector functionality"""

    collector = ObservabilityCollector()

    # Test collecting pipeline execution metrics from dict
    execution_summary = {
        'execution_id': 'test-execution',
        'date': '2023-01-01',
        'start_time': '2023-01-01T10:00:00',
        'end_time': '2023-01-01T10:05:00',
        'status': 'completed',
        'stage_count': 3,
        'successful_stages': 3,
        'failed_stages': 0,
        'overall_result': 'success'
    }

    pipeline_metrics = collector.collect_pipeline_execution_metrics(execution_summary)
    assert pipeline_metrics.execution_id == 'test-execution'
    assert pipeline_metrics.execution_status.value == 'COMPLETED'

    # Test collecting stage metrics from dict
    stage_summary = {
        'execution_id': 'test-execution',
        'stage_name': 'test-stage',
        'start_time': '2023-01-01T10:00:00',
        'end_time': '2023-01-01T10:01:00',
        'status': 'completed',
        'input_record_count': 1000,
        'output_record_count': 950
    }

    stage_metrics = collector.collect_stage_metrics(stage_summary)
    assert stage_metrics.stage_name == 'test-stage'
    assert stage_metrics.stage_status.value == 'COMPLETED'


def test_metrics_service():
    """Test observability metrics service functionality"""

    metrics_service = ObservabilityMetricsService()

    # Test empty calculations
    execution_rates = metrics_service.calculate_execution_rates([])
    assert execution_rates['success_rate'] == 0.0
    assert execution_rates['failure_rate'] == 0.0

    # Test with sample data
    pipeline_metrics = PipelineExecutionMetrics(
        execution_id="exec-123",
        pipeline_date="2023-01-01",
        start_timestamp=datetime.now(),
        end_timestamp=None,
        duration_seconds=300.0,
        execution_status=ExecutionStatus.COMPLETED,
        stage_count=3,
        successful_stages=3,
        failed_stages=0,
        overall_result="success"
    )

    stage_metrics = StageMetrics(
        execution_id="exec-123",
        stage_name="test-stage",
        start_timestamp=datetime.now(),
        end_timestamp=None,
        duration_seconds=60.0,
        stage_status=StageStatus.COMPLETED
    )

    # These should not throw exceptions
    metrics_service.calculate_execution_rates([pipeline_metrics])
    metrics_service.calculate_stage_durations([stage_metrics])


if __name__ == "__main__":
    test_models_creation()
    test_collector_functions()
    test_metrics_service()
    print("All tests passed!")