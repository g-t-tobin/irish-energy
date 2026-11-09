"""
Historical data inventory models for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class DataLayer(Enum):
    """Enumeration of data layers"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"


class ReconciliationStatus(Enum):
    """Enumeration of reconciliation statuses"""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


@dataclass
class HistoricalDatasetInfo:
    """Information about a specific dataset in the data lake"""
    dataset_name: str
    data_layer: DataLayer
    earliest_available_date: Optional[datetime]
    latest_available_date: Optional[datetime]
    available_partitions: List[str]  # List of date strings in YYYY-MM-DD format
    missing_partitions: List[str]  # List of expected date strings that are missing
    record_counts: Dict[str, int]  # Partition date -> record count mapping
    file_counts: Dict[str, int]  # Partition date -> file count mapping
    total_file_sizes: Dict[str, int]  # Partition date -> total file size in bytes
    schema_info: Optional[Dict[str, Any]]  # Schema information for the dataset


@dataclass
class ReconciliationReport:
    """Report from a reconciliation operation"""
    reconciliation_id: str
    dataset_name: str
    date_range: Optional[tuple]  # (start_date, end_date) as strings
    data_layer: DataLayer
    assessment_timestamp: datetime
    overall_status: ReconciliationStatus
    missing_dates: List[str]
    incomplete_dates: List[str]
    record_count_differences: Dict[str, Dict[str, Union[int, str]]]  # Partition -> {bronze_count, silver_count, difference}
    quality_issues: List[str]
    identified_discrepancies: List[str]
    recommended_actions: List[str]


class DatasetInventory(TypedDict):
    """Typed dictionary for dataset inventory"""
    dataset_name: str
    data_layer: str
    earliest_available_date: Optional[str]
    latest_available_date: Optional[str]
    available_partitions: List[str]
    missing_partitions: List[str]
    record_counts: Dict[str, int]
    file_counts: Dict[str, int]
    total_file_sizes: Dict[str, int]
    schema_info: Optional[Dict[str, Any]]


class ReconciliationReportDict(TypedDict):
    """Typed dictionary for reconciliation report"""
    reconciliation_id: str
    dataset_name: str
    date_range: Optional[tuple]
    data_layer: str
    assessment_timestamp: str
    overall_status: str
    missing_dates: List[str]
    incomplete_dates: List[str]
    record_count_differences: Dict[str, Dict[str, Union[int, str]]]
    quality_issues: List[str]
    identified_discrepancies: List[str]
    recommended_actions: List[str]