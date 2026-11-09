"""
Observability data models for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class ExecutionStatus(Enum):
    """Enumeration of execution statuses"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class StageStatus(Enum):
    """Enumeration of stage statuses"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class FreshnessStatus(Enum):
    """Enumeration of freshness statuses"""
    FRESH = "FRESH"
    DELAYED = "DELAYED"
    STALE = "STALE"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class QualityStatus(Enum):
    """Enumeration of quality statuses"""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


@dataclass
class PipelineExecutionMetrics:
    """Metrics for a complete pipeline execution"""
    execution_id: str
    pipeline_date: str
    start_timestamp: datetime
    end_timestamp: Optional[datetime]
    duration_seconds: Optional[float]
    execution_status: ExecutionStatus
    stage_count: int
    successful_stages: int
    failed_stages: int
    overall_result: str
    error_message: Optional[str] = None
    stage_metrics: List['StageMetrics'] = None


@dataclass
class StageMetrics:
    """Metrics for a single processing stage"""
    execution_id: str
    stage_name: str
    start_timestamp: Optional[datetime]
    end_timestamp: Optional[datetime]
    duration_seconds: Optional[float]
    stage_status: StageStatus
    input_record_count: Optional[int] = None
    output_record_count: Optional[int] = None
    error_classification: Optional[str] = None
    retry_count: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class DatasetMetrics:
    """Metrics for a dataset at a specific layer"""
    dataset_name: str
    data_layer: str
    partition_date: str
    record_count: int
    file_count: int
    total_file_size_bytes: int
    latest_timestamp: Optional[datetime]
    earliest_timestamp: Optional[datetime]
    last_successful_processing: Optional[datetime]


@dataclass
class DatasetFreshnessMetrics:
    """Freshness metrics for a dataset"""
    dataset_name: str
    expected_update_frequency: str  # e.g., "daily", "hourly"
    last_successful_ingestion: Optional[datetime]
    last_successful_transformation: Optional[datetime]
    data_age_days: Optional[float]
    freshness_status: FreshnessStatus
    freshness_threshold_days: int
    last_assessment_timestamp: datetime


@dataclass
class QualityMetrics:
    """Quality metrics from Phase 3.1 framework"""
    dataset_name: str
    data_layer: str
    pipeline_date: str
    assessment_timestamp: datetime
    total_records: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    overall_score: float
    quality_status: QualityStatus
    explanation: Optional[str] = None


@dataclass
class DataLineage:
    """Data lineage representation"""
    dataset_name: str
    data_layer: str
    partition_date: str
    source: str
    pipeline_execution_id: str
    processing_stage: str
    input_dataset: Optional[str]
    output_dataset: Optional[str]
    processing_timestamp: datetime
    quality_assessment_ref: Optional[str]


class PipelineExecutionSummary(TypedDict):
    """Typed dictionary for pipeline execution summary"""
    execution_id: str
    pipeline_date: str
    start_timestamp: str
    end_timestamp: Optional[str]
    duration_seconds: Optional[float]
    execution_status: str
    stage_count: int
    successful_stages: int
    failed_stages: int
    overall_result: str
    error_message: Optional[str]


class StageExecutionSummary(TypedDict):
    """Typed dictionary for stage execution summary"""
    execution_id: str
    stage_name: str
    start_timestamp: Optional[str]
    end_timestamp: Optional[str]
    duration_seconds: Optional[float]
    stage_status: str
    input_record_count: Optional[int]
    output_record_count: Optional[int]
    error_classification: Optional[str]
    retry_count: Optional[int]
    error_message: Optional[str]


class DatasetSummary(TypedDict):
    """Typed dictionary for dataset summary"""
    dataset_name: str
    data_layer: str
    partition_date: str
    record_count: int
    file_count: int
    total_file_size_bytes: int
    latest_timestamp: Optional[str]
    earliest_timestamp: Optional[str]
    last_successful_processing: Optional[str]