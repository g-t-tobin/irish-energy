"""
Observability collector for Irish Energy Analytics Data Platform
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from loguru import logger
from .models import (
    PipelineExecutionMetrics, StageMetrics, DatasetMetrics, DatasetFreshnessMetrics,
    QualityMetrics, DataLineage, ExecutionStatus, StageStatus, FreshnessStatus, QualityStatus
)
from src.quality.models import QualityReport


class ObservabilityCollector:
    """
    Collects and aggregates operational information from existing pipeline components
    """

    def __init__(self):
        # This collector will work with existing data sources
        # It doesn't create new resources, just aggregates existing information
        pass

    def collect_pipeline_execution_metrics(self, execution_summary: Dict[str, Any]) -> PipelineExecutionMetrics:
        """
        Collect metrics from a pipeline execution summary

        Args:
            execution_summary: Dictionary with execution summary data

        Returns:
            PipelineExecutionMetrics object
        """
        # Parse timestamps
        start_timestamp = datetime.fromisoformat(execution_summary['start_time']) if execution_summary.get('start_time') else None
        end_timestamp = datetime.fromisoformat(execution_summary['end_time']) if execution_summary.get('end_time') else None

        # Calculate duration
        duration_seconds = None
        if start_timestamp and end_timestamp:
            duration_seconds = (end_timestamp - start_timestamp).total_seconds()

        # Determine status
        status_str = execution_summary.get('status', 'unknown')
        try:
            execution_status = ExecutionStatus(status_str.upper())
        except ValueError:
            execution_status = ExecutionStatus.UNKNOWN

        # Create the metrics object
        metrics = PipelineExecutionMetrics(
            execution_id=execution_summary.get('execution_id', ''),
            pipeline_date=execution_summary.get('date', ''),
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            duration_seconds=duration_seconds,
            execution_status=execution_status,
            stage_count=execution_summary.get('stage_count', 0),
            successful_stages=execution_summary.get('successful_stages', 0),
            failed_stages=execution_summary.get('failed_stages', 0),
            overall_result=execution_summary.get('overall_result', 'unknown'),
            error_message=execution_summary.get('error_message')
        )

        return metrics

    def collect_stage_metrics(self, stage_summary: Dict[str, Any]) -> StageMetrics:
        """
        Collect metrics from a stage execution summary

        Args:
            stage_summary: Dictionary with stage summary data

        Returns:
            StageMetrics object
        """
        # Parse timestamps
        start_timestamp = datetime.fromisoformat(stage_summary['start_time']) if stage_summary.get('start_time') else None
        end_timestamp = datetime.fromisoformat(stage_summary['end_time']) if stage_summary.get('end_time') else None

        # Calculate duration
        duration_seconds = None
        if start_timestamp and end_timestamp:
            duration_seconds = (end_timestamp - start_timestamp).total_seconds()

        # Determine status
        status_str = stage_summary.get('status', 'unknown')
        try:
            stage_status = StageStatus(status_str.upper())
        except ValueError:
            stage_status = StageStatus.UNKNOWN

        # Create the metrics object
        metrics = StageMetrics(
            execution_id=stage_summary.get('execution_id', ''),
            stage_name=stage_summary.get('stage_name', ''),
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            duration_seconds=duration_seconds,
            stage_status=stage_status,
            input_record_count=stage_summary.get('input_record_count'),
            output_record_count=stage_summary.get('output_record_count'),
            error_classification=stage_summary.get('error_classification'),
            retry_count=stage_summary.get('retry_count'),
            error_message=stage_summary.get('error_message')
        )

        return metrics

    def collect_dataset_metrics(self, dataset_info: Dict[str, Any]) -> DatasetMetrics:
        """
        Collect metrics from dataset information

        Args:
            dataset_info: Dictionary with dataset information

        Returns:
            DatasetMetrics object
        """
        # Parse timestamps
        latest_timestamp = datetime.fromisoformat(dataset_info['latest_timestamp']) if dataset_info.get('latest_timestamp') else None
        earliest_timestamp = datetime.fromisoformat(dataset_info['earliest_timestamp']) if dataset_info.get('earliest_timestamp') else None
        last_successful_processing = datetime.fromisoformat(dataset_info['last_successful_processing']) if dataset_info.get('last_successful_processing') else None

        # Create the metrics object
        metrics = DatasetMetrics(
            dataset_name=dataset_info.get('dataset_name', ''),
            data_layer=dataset_info.get('data_layer', ''),
            partition_date=dataset_info.get('partition_date', ''),
            record_count=dataset_info.get('record_count', 0),
            file_count=dataset_info.get('file_count', 0),
            total_file_size_bytes=dataset_info.get('total_file_size_bytes', 0),
            latest_timestamp=latest_timestamp,
            earliest_timestamp=earliest_timestamp,
            last_successful_processing=last_successful_processing
        )

        return metrics

    def collect_quality_metrics(self, quality_report: QualityReport) -> QualityMetrics:
        """
        Collect quality metrics from a quality report

        Args:
            quality_report: QualityReport object

        Returns:
            QualityMetrics object
        """
        # Convert quality report to metrics
        metrics = QualityMetrics(
            dataset_name=quality_report.dataset_name,
            data_layer=quality_report.data_layer,
            pipeline_date=quality_report.pipeline_date,
            assessment_timestamp=quality_report.assessment_timestamp,
            total_records=quality_report.total_records,
            passed_checks=quality_report.passed_checks,
            failed_checks=quality_report.failed_checks,
            warning_checks=quality_report.warning_checks,
            overall_score=quality_report.overall_score,
            quality_status=quality_report.quality_status,
            explanation=quality_report.explanation
        )

        return metrics

    def collect_freshness_metrics(self, dataset_name: str,
                                 last_ingestion: Optional[datetime],
                                 last_transformation: Optional[datetime],
                                 expected_frequency: str = "daily",
                                 freshness_threshold_days: int = 2) -> DatasetFreshnessMetrics:
        """
        Collect freshness metrics for a dataset

        Args:
            dataset_name: Name of the dataset
            last_ingestion: Timestamp of last successful ingestion
            last_transformation: Timestamp of last successful transformation
            expected_frequency: Expected update frequency
            freshness_threshold_days: Threshold for stale data in days

        Returns:
            DatasetFreshnessMetrics object
        """
        # Get current time for age calculation
        current_time = datetime.now(timezone.utc)

        # Determine data age
        data_age_days = None
        if last_ingestion:
            data_age_days = (current_time - last_ingestion).days
        elif last_transformation:
            data_age_days = (current_time - last_transformation).days

        # Determine freshness status
        freshness_status = FreshnessStatus.UNKNOWN
        if data_age_days is not None:
            if data_age_days <= 1:
                freshness_status = FreshnessStatus.FRESH
            elif data_age_days <= freshness_threshold_days:
                freshness_status = FreshnessStatus.DELAYED
            elif data_age_days > freshness_threshold_days:
                freshness_status = FreshnessStatus.STALE
        elif last_ingestion is None and last_transformation is None:
            freshness_status = FreshnessStatus.MISSING

        # Create the metrics object
        metrics = DatasetFreshnessMetrics(
            dataset_name=dataset_name,
            expected_update_frequency=expected_frequency,
            last_successful_ingestion=last_ingestion,
            last_successful_transformation=last_transformation,
            data_age_days=data_age_days,
            freshness_status=freshness_status,
            freshness_threshold_days=freshness_threshold_days,
            last_assessment_timestamp=current_time
        )

        return metrics

    def collect_lineage(self, dataset_name: str, data_layer: str, partition_date: str,
                       source: str, pipeline_execution_id: str, processing_stage: str,
                       input_dataset: Optional[str] = None,
                       output_dataset: Optional[str] = None,
                       quality_assessment_ref: Optional[str] = None) -> DataLineage:
        """
        Collect lineage information for a dataset

        Args:
            dataset_name: Name of the dataset
            data_layer: Layer (bronze, silver, gold)
            partition_date: Date partition
            source: Source of the data
            pipeline_execution_id: Execution ID
            processing_stage: Stage of processing
            input_dataset: Input dataset name (if applicable)
            output_dataset: Output dataset name (if applicable)
            quality_assessment_ref: Quality assessment reference (if applicable)

        Returns:
            DataLineage object
        """
        # Create the lineage object
        lineage = DataLineage(
            dataset_name=dataset_name,
            data_layer=data_layer,
            partition_date=partition_date,
            source=source,
            pipeline_execution_id=pipeline_execution_id,
            processing_stage=processing_stage,
            input_dataset=input_dataset,
            output_dataset=output_dataset,
            processing_timestamp=datetime.now(timezone.utc),
            quality_assessment_ref=quality_assessment_ref
        )

        return lineage