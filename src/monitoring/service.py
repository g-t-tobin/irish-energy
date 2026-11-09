"""
Monitoring service for Irish Energy Analytics Platform
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
from src.common.config import Config

# Import storage interfaces here to avoid circular imports
from src.monitoring.storage_interface import MonitoringStorageInterface
from src.monitoring.local_storage import LocalMonitoringStorage
from src.monitoring.s3_storage import S3MonitoringStorage

# Import observability models
from src.observability.models import (
    PipelineExecutionMetrics, StageMetrics, DatasetMetrics, DatasetFreshnessMetrics,
    QualityMetrics, DataLineage
)
from src.observability.collector import ObservabilityCollector
from src.observability.metrics import ObservabilityMetricsService

class MonitoringService:
    """
    Service for collecting and managing monitoring data
    """

    def __init__(self):
        self.config = Config()
        self.storage = self._create_storage_backend()
        # Don't import QualityChecker here to avoid pulling in transformation dependencies
        self._quality_checker = None
        # Initialize observability components
        self.observability_collector = ObservabilityCollector()
        self.observability_metrics = ObservabilityMetricsService()

    def _create_storage_backend(self) -> MonitoringStorageInterface:
        """Create the appropriate storage backend based on configuration"""
        storage_backend = self.config.STORAGE_BACKEND.lower()

        if storage_backend == 's3':
            # For S3, use the BRONZE_BUCKET with monitoring prefix
            return S3MonitoringStorage(bucket_name=self.config.BRONZE_BUCKET, prefix="monitoring/")
        else:  # Default to local storage
            return LocalMonitoringStorage()

    def _get_quality_checker(self):
        """Lazy load QualityChecker only when needed"""
        if self._quality_checker is None:
            from src.transformation.quality_checks import QualityChecker
            self._quality_checker = QualityChecker()
        return self._quality_checker

    def record_execution_start(self, data_type: str, date_str: str, source: str = "pipeline") -> str:
        """
        Record the start of an execution

        Args:
            data_type: Type of data being processed
            date_str: Date string for the data
            source: Source of the execution (pipeline, manual, etc.)

        Returns:
            Execution ID
        """
        execution_id = str(uuid.uuid4())

        summary = {
            'execution_id': execution_id,
            'data_type': data_type,
            'date': date_str,
            'source': source,
            'status': 'started',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': None,
            'error_message': None
        }

        self.storage.save_execution_summary(execution_id, summary)
        logger.info(f"Recorded execution start: {execution_id}")
        return execution_id

    def record_execution_success(self, execution_id: str, data_type: str, date_str: str,
                               source: str = "pipeline", duration_seconds: float = 0.0) -> bool:
        """
        Record successful completion of an execution

        Args:
            execution_id: Execution ID
            data_type: Type of data processed
            date_str: Date string for the data
            source: Source of the execution
            duration_seconds: Duration of execution in seconds

        Returns:
            True if successful, False otherwise
        """
        summary = self.storage.get_execution_summary(execution_id)
        if not summary:
            logger.error(f"Execution summary not found for {execution_id}")
            return False

        # Update summary with completion info
        summary.update({
            'data_type': data_type,
            'date': date_str,
            'status': 'completed',
            'end_time': datetime.now().isoformat(),
            'duration_seconds': duration_seconds,
            'error_message': None
        })

        success = self.storage.save_execution_summary(execution_id, summary)
        if success:
            logger.info(f"Recorded successful execution: {execution_id}")
        else:
            logger.error(f"Failed to record successful execution: {execution_id}")

        return success

    def record_execution_failure(self, execution_id: str, error_message: str,
                               data_type: str = None, date_str: str = None) -> bool:
        """
        Record failure of an execution

        Args:
            execution_id: Execution ID
            error_message: Error message
            data_type: Type of data (optional)
            date_str: Date string for the data (optional)

        Returns:
            True if successful, False otherwise
        """
        summary = self.storage.get_execution_summary(execution_id)
        if not summary:
            logger.error(f"Execution summary not found for {execution_id}")
            return False

        # Update summary with failure info, preserving existing metadata when not supplied
        failure_info = {
            'status': 'failed',
            'end_time': datetime.now().isoformat(),
            'error_message': error_message
        }
        if data_type is not None:
            failure_info['data_type'] = data_type
        if date_str is not None:
            failure_info['date'] = date_str
        summary.update(failure_info)

        success = self.storage.save_execution_summary(execution_id, summary)
        if success:
            logger.info(f"Recorded failed execution: {execution_id}")
        else:
            logger.error(f"Failed to record failed execution: {execution_id}")

        return success

    def generate_and_record_quality_report(self, data_type: str, data: Dict[str, Any],
                                         execution_id: str) -> str:
        """
        Generate quality report and save it

        Args:
            data_type: Type of data
            data: Raw data
            execution_id: Associated execution ID

        Returns:
            Report ID
        """
        try:
            # Lazy load QualityChecker only when needed
            quality_checker = self._get_quality_checker()
            # Generate quality report
            report = quality_checker.generate_quality_report(data_type, data)

            # Add execution reference
            report['execution_id'] = execution_id

            # Create report ID
            report_id = f"{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Save report
            success = self.storage.save_quality_report(report_id, report)
            if success:
                logger.info(f"Generated and recorded quality report: {report_id}")
            else:
                logger.error(f"Failed to record quality report: {report_id}")

            return report_id

        except Exception as e:
            logger.error(f"Error generating quality report: {str(e)}")
            return ""

    def get_execution_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution summary

        Args:
            execution_id: Execution ID

        Returns:
            Execution summary or None
        """
        return self.storage.get_execution_summary(execution_id)

    def get_quality_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve quality report

        Args:
            report_id: Report ID

        Returns:
            Quality report or None
        """
        return self.storage.get_quality_report(report_id)

    def get_recent_executions(self, limit: int = 20) -> list:
        """
        Get recent execution summaries

        Args:
            limit: Maximum number of summaries to return

        Returns:
            List of recent execution summaries
        """
        return self.storage.list_execution_summaries(limit)

    def get_recent_quality_reports(self, limit: int = 20) -> list:
        """
        Get recent quality reports

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of recent quality reports
        """
        return self.storage.list_quality_reports(limit)

    def save_observability_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Save observability metrics to storage

        Args:
            metrics: Dictionary with observability metrics

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a unique identifier for the observability data
            metrics_id = f"observability_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Add timestamp to metrics
            metrics_with_timestamp = {
                **metrics,
                'timestamp': datetime.now().isoformat(),
                'metrics_id': metrics_id
            }

            # Save to storage using a convention
            # We'll save it as a quality report for now to reuse existing infrastructure
            success = self.storage.save_quality_report(metrics_id, metrics_with_timestamp)
            if success:
                logger.info(f"Saved observability metrics: {metrics_id}")
            else:
                logger.error(f"Failed to save observability metrics: {metrics_id}")

            return success

        except Exception as e:
            logger.error(f"Error saving observability metrics: {str(e)}")
            return False

    def collect_and_save_pipeline_metrics(self, execution_id: str,
                                        pipeline_metrics: PipelineExecutionMetrics) -> bool:
        """
        Collect and save pipeline execution metrics

        Args:
            execution_id: Execution ID
            pipeline_metrics: Pipeline execution metrics

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert pipeline metrics to dict format for storage
            metrics_dict = {
                'type': 'pipeline_execution',
                'execution_id': pipeline_metrics.execution_id,
                'pipeline_date': pipeline_metrics.pipeline_date,
                'start_timestamp': pipeline_metrics.start_timestamp.isoformat() if pipeline_metrics.start_timestamp else None,
                'end_timestamp': pipeline_metrics.end_timestamp.isoformat() if pipeline_metrics.end_timestamp else None,
                'duration_seconds': pipeline_metrics.duration_seconds,
                'execution_status': pipeline_metrics.execution_status.value,
                'stage_count': pipeline_metrics.stage_count,
                'successful_stages': pipeline_metrics.successful_stages,
                'failed_stages': pipeline_metrics.failed_stages,
                'overall_result': pipeline_metrics.overall_result,
                'error_message': pipeline_metrics.error_message
            }

            return self.save_observability_metrics(metrics_dict)

        except Exception as e:
            logger.error(f"Error collecting pipeline metrics: {str(e)}")
            return False

    def collect_and_save_stage_metrics(self, stage_metrics: StageMetrics) -> bool:
        """
        Collect and save stage execution metrics

        Args:
            stage_metrics: Stage execution metrics

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert stage metrics to dict format for storage
            metrics_dict = {
                'type': 'stage_execution',
                'execution_id': stage_metrics.execution_id,
                'stage_name': stage_metrics.stage_name,
                'start_timestamp': stage_metrics.start_timestamp.isoformat() if stage_metrics.start_timestamp else None,
                'end_timestamp': stage_metrics.end_timestamp.isoformat() if stage_metrics.end_timestamp else None,
                'duration_seconds': stage_metrics.duration_seconds,
                'stage_status': stage_metrics.stage_status.value,
                'input_record_count': stage_metrics.input_record_count,
                'output_record_count': stage_metrics.output_record_count,
                'error_classification': stage_metrics.error_classification,
                'retry_count': stage_metrics.retry_count,
                'error_message': stage_metrics.error_message
            }

            return self.save_observability_metrics(metrics_dict)

        except Exception as e:
            logger.error(f"Error collecting stage metrics: {str(e)}")
            return False

    def collect_and_save_dataset_metrics(self, dataset_metrics: DatasetMetrics) -> bool:
        """
        Collect and save dataset metrics

        Args:
            dataset_metrics: Dataset metrics

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert dataset metrics to dict format for storage
            metrics_dict = {
                'type': 'dataset_metrics',
                'dataset_name': dataset_metrics.dataset_name,
                'data_layer': dataset_metrics.data_layer,
                'partition_date': dataset_metrics.partition_date,
                'record_count': dataset_metrics.record_count,
                'file_count': dataset_metrics.file_count,
                'total_file_size_bytes': dataset_metrics.total_file_size_bytes,
                'latest_timestamp': dataset_metrics.latest_timestamp.isoformat() if dataset_metrics.latest_timestamp else None,
                'earliest_timestamp': dataset_metrics.earliest_timestamp.isoformat() if dataset_metrics.earliest_timestamp else None,
                'last_successful_processing': dataset_metrics.last_successful_processing.isoformat() if dataset_metrics.last_successful_processing else None
            }

            return self.save_observability_metrics(metrics_dict)

        except Exception as e:
            logger.error(f"Error collecting dataset metrics: {str(e)}")
            return False

    def collect_and_save_freshness_metrics(self, freshness_metrics: DatasetFreshnessMetrics) -> bool:
        """
        Collect and save freshness metrics

        Args:
            freshness_metrics: Dataset freshness metrics

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert freshness metrics to dict format for storage
            metrics_dict = {
                'type': 'dataset_freshness',
                'dataset_name': freshness_metrics.dataset_name,
                'expected_update_frequency': freshness_metrics.expected_update_frequency,
                'last_successful_ingestion': freshness_metrics.last_successful_ingestion.isoformat() if freshness_metrics.last_successful_ingestion else None,
                'last_successful_transformation': freshness_metrics.last_successful_transformation.isoformat() if freshness_metrics.last_successful_transformation else None,
                'data_age_days': freshness_metrics.data_age_days,
                'freshness_status': freshness_metrics.freshness_status.value,
                'freshness_threshold_days': freshness_metrics.freshness_threshold_days,
                'last_assessment_timestamp': freshness_metrics.last_assessment_timestamp.isoformat()
            }

            return self.save_observability_metrics(metrics_dict)

        except Exception as e:
            logger.error(f"Error collecting freshness metrics: {str(e)}")
            return False

    def collect_and_save_quality_metrics(self, quality_metrics: QualityMetrics) -> bool:
        """
        Collect and save quality metrics

        Args:
            quality_metrics: Quality metrics

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert quality metrics to dict format for storage
            metrics_dict = {
                'type': 'quality_metrics',
                'dataset_name': quality_metrics.dataset_name,
                'data_layer': quality_metrics.data_layer,
                'pipeline_date': quality_metrics.pipeline_date,
                'assessment_timestamp': quality_metrics.assessment_timestamp.isoformat(),
                'total_records': quality_metrics.total_records,
                'passed_checks': quality_metrics.passed_checks,
                'failed_checks': quality_metrics.failed_checks,
                'warning_checks': quality_metrics.warning_checks,
                'overall_score': quality_metrics.overall_score,
                'quality_status': quality_metrics.quality_status.value,
                'explanation': quality_metrics.explanation
            }

            return self.save_observability_metrics(metrics_dict)

        except Exception as e:
            logger.error(f"Error collecting quality metrics: {str(e)}")
            return False

    def collect_and_save_lineage(self, lineage: DataLineage) -> bool:
        """
        Collect and save data lineage information

        Args:
            lineage: Data lineage information

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert lineage to dict format for storage
            metrics_dict = {
                'type': 'data_lineage',
                'dataset_name': lineage.dataset_name,
                'data_layer': lineage.data_layer,
                'partition_date': lineage.partition_date,
                'source': lineage.source,
                'pipeline_execution_id': lineage.pipeline_execution_id,
                'processing_stage': lineage.processing_stage,
                'input_dataset': lineage.input_dataset,
                'output_dataset': lineage.output_dataset,
                'processing_timestamp': lineage.processing_timestamp.isoformat(),
                'quality_assessment_ref': lineage.quality_assessment_ref
            }

            return self.save_observability_metrics(metrics_dict)

        except Exception as e:
            logger.error(f"Error collecting lineage: {str(e)}")
            return False