"""
Observability metrics service for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from loguru import logger
from .models import (
    PipelineExecutionMetrics, StageMetrics, DatasetMetrics, DatasetFreshnessMetrics,
    QualityMetrics, DataLineage, ExecutionStatus, StageStatus, FreshnessStatus, QualityStatus
)
from .collector import ObservabilityCollector


class ObservabilityMetricsService:
    """
    Service for aggregating and calculating observability metrics
    """

    def __init__(self):
        self.collector = ObservabilityCollector()

    def calculate_execution_rates(self, executions: List[PipelineExecutionMetrics]) -> Dict[str, float]:
        """
        Calculate execution success and failure rates

        Args:
            executions: List of pipeline execution metrics

        Returns:
            Dictionary with success rate and failure rate
        """
        if not executions:
            return {'success_rate': 0.0, 'failure_rate': 0.0}

        total_executions = len(executions)
        successful_executions = sum(1 for exec_metrics in executions
                                  if exec_metrics.execution_status == ExecutionStatus.COMPLETED)
        failed_executions = sum(1 for exec_metrics in executions
                               if exec_metrics.execution_status == ExecutionStatus.FAILED)

        success_rate = (successful_executions / total_executions) * 100 if total_executions > 0 else 0.0
        failure_rate = (failed_executions / total_executions) * 100 if total_executions > 0 else 0.0

        return {
            'success_rate': round(success_rate, 2),
            'failure_rate': round(failure_rate, 2)
        }

    def calculate_stage_durations(self, stages: List[StageMetrics]) -> Dict[str, Union[float, int]]:
        """
        Calculate stage duration statistics

        Args:
            stages: List of stage metrics

        Returns:
            Dictionary with duration statistics
        """
        if not stages:
            return {
                'average_duration': 0.0,
                'min_duration': 0,
                'max_duration': 0,
                'median_duration': 0
            }

        # Filter out stages with valid duration data
        valid_durations = [stage.duration_seconds for stage in stages
                          if stage.duration_seconds is not None and stage.duration_seconds >= 0]

        if not valid_durations:
            return {
                'average_duration': 0.0,
                'min_duration': 0,
                'max_duration': 0,
                'median_duration': 0
            }

        # Calculate statistics
        avg_duration = sum(valid_durations) / len(valid_durations)
        min_duration = min(valid_durations)
        max_duration = max(valid_durations)
        median_duration = sorted(valid_durations)[len(valid_durations) // 2]

        return {
            'average_duration': round(avg_duration, 2),
            'min_duration': min_duration,
            'max_duration': max_duration,
            'median_duration': median_duration
        }

    def calculate_dataset_volume(self, datasets: List[DatasetMetrics]) -> Dict[str, Union[int, float]]:
        """
        Calculate total dataset volume metrics

        Args:
            datasets: List of dataset metrics

        Returns:
            Dictionary with volume metrics
        """
        if not datasets:
            return {
                'total_records': 0,
                'total_files': 0,
                'total_size_bytes': 0
            }

        total_records = sum(dataset.record_count for dataset in datasets)
        total_files = sum(dataset.file_count for dataset in datasets)
        total_size_bytes = sum(dataset.total_file_size_bytes for dataset in datasets)

        return {
            'total_records': total_records,
            'total_files': total_files,
            'total_size_bytes': total_size_bytes
        }

    def calculate_freshness_trends(self, freshness_metrics: List[DatasetFreshnessMetrics]) -> Dict[str, Any]:
        """
        Calculate freshness trends

        Args:
            freshness_metrics: List of freshness metrics

        Returns:
            Dictionary with freshness trends
        """
        if not freshness_metrics:
            return {
                'fresh_datasets': 0,
                'delayed_datasets': 0,
                'stale_datasets': 0,
                'missing_datasets': 0,
                'unknown_datasets': 0
            }

        # Count freshness statuses
        freshness_counts = defaultdict(int)
        for freshness in freshness_metrics:
            freshness_counts[freshness.freshness_status] += 1

        return {
            'fresh_datasets': freshness_counts[FreshnessStatus.FRESH],
            'delayed_datasets': freshness_counts[FreshnessStatus.DELAYED],
            'stale_datasets': freshness_counts[FreshnessStatus.STALE],
            'missing_datasets': freshness_counts[FreshnessStatus.MISSING],
            'unknown_datasets': freshness_counts[FreshnessStatus.UNKNOWN]
        }

    def calculate_quality_trends(self, quality_metrics: List[QualityMetrics]) -> Dict[str, Union[float, int]]:
        """
        Calculate quality trends

        Args:
            quality_metrics: List of quality metrics

        Returns:
            Dictionary with quality trends
        """
        if not quality_metrics:
            return {
                'average_score': 0.0,
                'total_assessments': 0,
                'passing_assessments': 0,
                'warning_assessments': 0,
                'failing_assessments': 0
            }

        total_scores = sum(qm.overall_score for qm in quality_metrics)
        average_score = total_scores / len(quality_metrics)

        # Count quality statuses
        passing = sum(1 for qm in quality_metrics if qm.quality_status == QualityStatus.PASS)
        warning = sum(1 for qm in quality_metrics if qm.quality_status == QualityStatus.WARNING)
        failing = sum(1 for qm in quality_metrics if qm.quality_status == QualityStatus.FAIL)

        return {
            'average_score': round(average_score, 2),
            'total_assessments': len(quality_metrics),
            'passing_assessments': passing,
            'warning_assessments': warning,
            'failing_assessments': failing
        }

    def aggregate_executions_by_time_window(self, executions: List[PipelineExecutionMetrics],
                                          window_hours: int = 24) -> List[PipelineExecutionMetrics]:
        """
        Filter executions by time window

        Args:
            executions: List of pipeline execution metrics
            window_hours: Time window in hours

        Returns:
            List of executions within the time window
        """
        if not executions:
            return []

        # Calculate cutoff time
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        # Filter executions
        filtered_executions = [
            exec_metrics for exec_metrics in executions
            if exec_metrics.start_timestamp and exec_metrics.start_timestamp >= cutoff_time
        ]

        return filtered_executions