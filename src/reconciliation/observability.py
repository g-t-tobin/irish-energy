"""
Integration with observability framework for reconciliation and backfill
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from src.reconciliation.models import ReconciliationReport, DataLayer, ReconciliationStatus
from src.reconciliation.engine import ReconciliationEngine
from src.reconciliation.backfill import BackfillPlan
from src.observability.models import PipelineExecutionMetrics, StageMetrics, DatasetMetrics, DatasetFreshnessMetrics, QualityMetrics, DataLineage
from src.observability.collector import ObservabilityCollector
from src.observability.metrics import ObservabilityMetricsService


class ObservabilityIntegration:
    """
    Integration with observability framework for reconciliation and backfill metrics
    """

    def __init__(self):
        self.collector = ObservabilityCollector()
        self.metrics_service = ObservabilityMetricsService()

    def generate_reconciliation_metrics(self, reconciliation_report: ReconciliationReport) -> Dict[str, Any]:
        """
        Generate observability metrics from a reconciliation report

        Args:
            reconciliation_report: Reconciliation report to process

        Returns:
            Dictionary with reconciliation metrics
        """
        try:
            metrics = {
                'reconciliation_id': reconciliation_report.reconciliation_id,
                'dataset_name': reconciliation_report.dataset_name,
                'date_range': reconciliation_report.date_range,
                'assessment_timestamp': reconciliation_report.assessment_timestamp.isoformat(),
                'missing_dates_count': len(reconciliation_report.missing_dates),
                'incomplete_dates_count': len(reconciliation_report.incomplete_dates),
                'overall_status': reconciliation_report.overall_status.value,
                'record_count_differences_count': len(reconciliation_report.record_count_differences),
                'quality_issues_count': len(reconciliation_report.quality_issues),
                'discrepancies_count': len(reconciliation_report.identified_discrepancies)
            }

            return metrics
        except Exception as e:
            logger.error(f"Error generating reconciliation metrics: {str(e)}")
            return {}

    def generate_backfill_metrics(self, backfill_plan: BackfillPlan) -> Dict[str, Any]:
        """
        Generate observability metrics from a backfill plan

        Args:
            backfill_plan: Backfill plan to process

        Returns:
            Dictionary with backfill metrics
        """
        try:
            metrics = {
                'backfill_id': backfill_plan.backfill_id,
                'dataset_name': backfill_plan.dataset_name,
                'date_range': backfill_plan.date_range,
                'missing_partitions_count': len(backfill_plan.missing_partitions),
                'required_stages': backfill_plan.required_stages,
                'estimated_workload': backfill_plan.estimated_workload,
                'risks_count': len(backfill_plan.identified_risks),
                'dry_run_mode': backfill_plan.dry_run
            }

            return metrics
        except Exception as e:
            logger.error(f"Error generating backfill metrics: {str(e)}")
            return {}

    def generate_dataset_metrics(self, dataset_name: str, data_layer: DataLayer,
                               available_partitions: List[str], missing_partitions: List[str]) -> DatasetMetrics:
        """
        Generate dataset metrics for observability

        Args:
            dataset_name: Name of the dataset
            data_layer: Data layer (bronze, silver, gold)
            available_partitions: List of available partition dates
            missing_partitions: List of missing partition dates

        Returns:
            DatasetMetrics object
        """
        try:
            # Calculate basic stats
            record_count = len(available_partitions) * 1000  # Placeholder value
            file_count = len(available_partitions) * 2  # Placeholder value
            total_file_size = len(available_partitions) * 1024000  # Placeholder value

            # Create timestamp for latest processing
            latest_timestamp = datetime.now()
            earliest_timestamp = datetime.now()  # Placeholder

            # Create and return dataset metrics
            return DatasetMetrics(
                dataset_name=dataset_name,
                data_layer=data_layer.value,
                partition_date=available_partitions[0] if available_partitions else '',
                record_count=record_count,
                file_count=file_count,
                total_file_size_bytes=total_file_size,
                latest_timestamp=latest_timestamp,
                earliest_timestamp=earliest_timestamp,
                last_successful_processing=latest_timestamp
            )
        except Exception as e:
            logger.error(f"Error generating dataset metrics for {dataset_name}: {str(e)}")
            # Return a minimal dataset metrics object
            return DatasetMetrics(
                dataset_name=dataset_name,
                data_layer=data_layer.value,
                partition_date='',
                record_count=0,
                file_count=0,
                total_file_size_bytes=0,
                latest_timestamp=None,
                earliest_timestamp=None,
                last_successful_processing=None
            )

    def generate_freshness_metrics(self, dataset_name: str,
                                 last_successful_ingestion: Optional[datetime],
                                 last_successful_transformation: Optional[datetime],
                                 expected_frequency: str = "daily") -> DatasetFreshnessMetrics:
        """
        Generate freshness metrics for observability

        Args:
            dataset_name: Name of the dataset
            last_successful_ingestion: Timestamp of last successful ingestion
            last_successful_transformation: Timestamp of last successful transformation
            expected_frequency: Expected update frequency

        Returns:
            DatasetFreshnessMetrics object
        """
        try:
            # For demo purposes, we'll just create a basic freshness metric
            current_time = datetime.now()
            data_age_days = 0.0  # Placeholder

            # Determine freshness status (simplified)
            freshness_status = "FRESH"  # Placeholder

            return DatasetFreshnessMetrics(
                dataset_name=dataset_name,
                expected_update_frequency=expected_frequency,
                last_successful_ingestion=last_successful_ingestion,
                last_successful_transformation=last_successful_transformation,
                data_age_days=data_age_days,
                freshness_status=freshness_status,
                freshness_threshold_days=2,
                last_assessment_timestamp=current_time
            )
        except Exception as e:
            logger.error(f"Error generating freshness metrics for {dataset_name}: {str(e)}")
            # Return a minimal freshness metrics object
            return DatasetFreshnessMetrics(
                dataset_name=dataset_name,
                expected_update_frequency=expected_frequency,
                last_successful_ingestion=None,
                last_successful_transformation=None,
                data_age_days=0.0,
                freshness_status="UNKNOWN",
                freshness_threshold_days=2,
                last_assessment_timestamp=datetime.now()
            )