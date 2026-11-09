"""
Abstract monitoring storage interface for Irish Energy Analytics Platform
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class MonitoringStorageInterface(ABC):
    """
    Abstract interface for monitoring data storage
    Both local and S3 implementations must adhere to this interface
    """

    @abstractmethod
    def save_execution_summary(self, execution_id: str, summary: Dict[str, Any]) -> bool:
        """
        Save execution summary to storage

        Args:
            execution_id: Unique identifier for the execution
            summary: Execution summary data

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def save_quality_report(self, report_id: str, report: Dict[str, Any]) -> bool:
        """
        Save quality report to storage

        Args:
            report_id: Unique identifier for the report
            report: Quality report data

        Returns:
            bool: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_execution_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution summary from storage

        Args:
            execution_id: Unique identifier for the execution

        Returns:
            Execution summary data or None if not found
        """
        pass

    @abstractmethod
    def get_quality_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve quality report from storage

        Args:
            report_id: Unique identifier for the report

        Returns:
            Quality report data or None if not found
        """
        pass

    @abstractmethod
    def list_execution_summaries(
        self,
        limit: int = 100,
        source_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        List execution summaries with optional filtering

        Args:
            limit: Maximum number of summaries to return
            source_filter: Filter by source (pipeline, manual, etc.)
            status_filter: Filter by status (started, completed, failed)
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of execution summaries
        """
        pass

    @abstractmethod
    def list_quality_reports(
        self,
        limit: int = 100,
        source_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        List quality reports with optional filtering

        Args:
            limit: Maximum number of reports to return
            source_filter: Filter by source
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of quality reports
        """
        pass