"""
Main observability service for Irish Energy Analytics Data Platform
This service integrates with the existing monitoring system to provide comprehensive observability
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from src.monitoring.service import MonitoringService
from src.observability.models import (
    PipelineExecutionMetrics, StageMetrics, DatasetMetrics, DatasetFreshnessMetrics,
    QualityMetrics, DataLineage
)
from src.observability.collector import ObservabilityCollector
from src.observability.metrics import ObservabilityMetricsService


class ObservabilityService:
    """
    Main observability service that coordinates data collection and reporting
    """

    def __init__(self, monitoring_service: MonitoringService = None):
        self.monitoring_service = monitoring_service or MonitoringService()
        self.collector = ObservabilityCollector()
        self.metrics_service = ObservabilityMetricsService()

    def record_pipeline_execution_start(self, execution_id: str, pipeline_date: str) -> bool:
        """
        Record the start of a pipeline execution

        Args:
            execution_id: Unique execution identifier
            pipeline_date: Date being processed

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create initial execution metrics
            metrics = PipelineExecutionMetrics(
                execution_id=execution_id,
                pipeline_date=pipeline_date,
                start_timestamp=datetime.now(),
                end_timestamp=None,
                duration_seconds=None,
                execution_status="RUNNING",
                stage_count=0,
                successful_stages=0,
                failed_stages=0,
                overall_result="running"
            )

            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_pipeline_metrics(execution_id, metrics)
            if success:
                logger.info(f"Recorded pipeline execution start: {execution_id}")
            else:
                logger.error(f"Failed to record pipeline execution start: {execution_id}")

            return success

        except Exception as e:
            logger.error(f"Error recording pipeline execution start: {str(e)}")
            return False

    def record_pipeline_execution_complete(self, execution_id: str, pipeline_date: str,
                                         duration_seconds: float,
                                         stage_count: int,
                                         successful_stages: int,
                                         failed_stages: int,
                                         overall_result: str,
                                         error_message: Optional[str] = None) -> bool:
        """
        Record successful completion of a pipeline execution

        Args:
            execution_id: Unique execution identifier
            pipeline_date: Date being processed
            duration_seconds: Duration of execution in seconds
            stage_count: Total number of stages
            successful_stages: Number of successful stages
            failed_stages: Number of failed stages
            overall_result: Overall execution result
            error_message: Error message if any

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create execution metrics
            metrics = PipelineExecutionMetrics(
                execution_id=execution_id,
                pipeline_date=pipeline_date,
                start_timestamp=None,  # Will be retrieved from existing record
                end_timestamp=datetime.now(),
                duration_seconds=duration_seconds,
                execution_status="COMPLETED",
                stage_count=stage_count,
                successful_stages=successful_stages,
                failed_stages=failed_stages,
                overall_result=overall_result,
                error_message=error_message
            )

            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_pipeline_metrics(execution_id, metrics)
            if success:
                logger.info(f"Recorded pipeline execution completion: {execution_id}")
            else:
                logger.error(f"Failed to record pipeline execution completion: {execution_id}")

            return success

        except Exception as e:
            logger.error(f"Error recording pipeline execution completion: {str(e)}")
            return False

    def record_stage_execution_start(self, execution_id: str, stage_name: str) -> bool:
        """
        Record the start of a stage execution

        Args:
            execution_id: Unique execution identifier
            stage_name: Name of the stage

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create stage metrics
            metrics = StageMetrics(
                execution_id=execution_id,
                stage_name=stage_name,
                start_timestamp=datetime.now(),
                end_timestamp=None,
                duration_seconds=None,
                stage_status="RUNNING",
                input_record_count=None,
                output_record_count=None,
                error_classification=None,
                retry_count=None,
                error_message=None
            )

            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_stage_metrics(metrics)
            if success:
                logger.info(f"Recorded stage execution start: {stage_name} for {execution_id}")
            else:
                logger.error(f"Failed to record stage execution start: {stage_name} for {execution_id}")

            return success

        except Exception as e:
            logger.error(f"Error recording stage execution start: {str(e)}")
            return False

    def record_stage_execution_complete(self, execution_id: str, stage_name: str,
                                      input_record_count: int, output_record_count: int,
                                      duration_seconds: float,
                                      stage_status: str = "COMPLETED",
                                      error_classification: Optional[str] = None,
                                      retry_count: Optional[int] = None,
                                      error_message: Optional[str] = None) -> bool:
        """
        Record completion of a stage execution

        Args:
            execution_id: Unique execution identifier
            stage_name: Name of the stage
            input_record_count: Number of records processed as input
            output_record_count: Number of records processed as output
            duration_seconds: Duration of execution in seconds
            stage_status: Status of the stage execution
            error_classification: Classification of any error (if applicable)
            retry_count: Number of retries (if applicable)
            error_message: Error message if any

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create stage metrics
            metrics = StageMetrics(
                execution_id=execution_id,
                stage_name=stage_name,
                start_timestamp=None,  # Will be retrieved from existing record
                end_timestamp=datetime.now(),
                duration_seconds=duration_seconds,
                stage_status=stage_status,
                input_record_count=input_record_count,
                output_record_count=output_record_count,
                error_classification=error_classification,
                retry_count=retry_count,
                error_message=error_message
            )

            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_stage_metrics(metrics)
            if success:
                logger.info(f"Recorded stage execution completion: {stage_name} for {execution_id}")
            else:
                logger.error(f"Failed to record stage execution completion: {stage_name} for {execution_id}")

            return success

        except Exception as e:
            logger.error(f"Error recording stage execution completion: {str(e)}")
            return False

    def record_dataset_metrics(self, dataset_metrics: DatasetMetrics) -> bool:
        """
        Record dataset metrics

        Args:
            dataset_metrics: Dataset metrics to record

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_dataset_metrics(dataset_metrics)
            if success:
                logger.info(f"Recorded dataset metrics for: {dataset_metrics.dataset_name}")
            else:
                logger.error(f"Failed to record dataset metrics for: {dataset_metrics.dataset_name}")

            return success

        except Exception as e:
            logger.error(f"Error recording dataset metrics: {str(e)}")
            return False

    def record_freshness_metrics(self, freshness_metrics: DatasetFreshnessMetrics) -> bool:
        """
        Record dataset freshness metrics

        Args:
            freshness_metrics: Freshness metrics to record

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_freshness_metrics(freshness_metrics)
            if success:
                logger.info(f"Recorded freshness metrics for: {freshness_metrics.dataset_name}")
            else:
                logger.error(f"Failed to record freshness metrics for: {freshness_metrics.dataset_name}")

            return success

        except Exception as e:
            logger.error(f"Error recording freshness metrics: {str(e)}")
            return False

    def record_quality_metrics(self, quality_metrics: QualityMetrics) -> bool:
        """
        Record quality metrics

        Args:
            quality_metrics: Quality metrics to record

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_quality_metrics(quality_metrics)
            if success:
                logger.info(f"Recorded quality metrics for: {quality_metrics.dataset_name}")
            else:
                logger.error(f"Failed to record quality metrics for: {quality_metrics.dataset_name}")

            return success

        except Exception as e:
            logger.error(f"Error recording quality metrics: {str(e)}")
            return False

    def record_data_lineage(self, lineage: DataLineage) -> bool:
        """
        Record data lineage information

        Args:
            lineage: Data lineage information to record

        Returns:
            True if successful, False otherwise
        """
        try:
            # Save to monitoring service
            success = self.monitoring_service.collect_and_save_lineage(lineage)
            if success:
                logger.info(f"Recorded data lineage for: {lineage.dataset_name}")
            else:
                logger.error(f"Failed to record data lineage for: {lineage.dataset_name}")

            return success

        except Exception as e:
            logger.error(f"Error recording data lineage: {str(e)}")
            return False

    def generate_aggregated_metrics_report(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Generate aggregated metrics report for a given time window

        Args:
            time_window_hours: Time window in hours to filter metrics

        Returns:
            Dictionary with aggregated metrics
        """
        try:
            # This method would typically query the monitoring storage for recent metrics
            # and compute aggregations. For now, we'll return a skeleton structure.
            report = {
                'generated_at': datetime.now().isoformat(),
                'time_window_hours': time_window_hours,
                'execution_rates': {},
                'stage_durations': {},
                'dataset_volumes': {},
                'freshness_trends': {},
                'quality_trends': {}
            }

            logger.info("Generated aggregated metrics report")
            return report

        except Exception as e:
            logger.error(f"Error generating aggregated metrics report: {str(e)}")
            return {}

    def get_recent_observability_data(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent observability data

        Args:
            limit: Maximum number of records to return

        Returns:
            List of recent observability data records
        """
        try:
            # For now, we'll use the quality reports list method as a proxy
            # In a real implementation, this would query the observability-specific storage
            return self.monitoring_service.storage.list_quality_reports(limit)

        except Exception as e:
            logger.error(f"Error retrieving recent observability data: {str(e)}")
            return []