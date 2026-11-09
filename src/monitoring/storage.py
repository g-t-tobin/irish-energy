"""
Monitoring data storage interface for Irish Energy Analytics Platform
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
from src.common.config import Config

class MonitoringStorage:
    """
    Storage interface for monitoring data (execution summaries and quality reports)
    Uses local file-based storage for local-only development
    """

    def __init__(self, storage_dir: str = None):
        self.config = Config()
        self.storage_dir = storage_dir or "./monitoring_data"

        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_execution_summary(self, execution_id: str, summary: Dict[str, Any]) -> bool:
        """
        Save execution summary to storage

        Args:
            execution_id: Unique identifier for the execution
            summary: Execution summary data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp to summary
            summary_with_timestamp = {
                **summary,
                'timestamp': datetime.now().isoformat()
            }

            # Create file path
            file_path = os.path.join(self.storage_dir, f"execution_{execution_id}.json")

            # Write to file
            with open(file_path, 'w') as f:
                json.dump(summary_with_timestamp, f, indent=2)

            logger.info(f"Saved execution summary for {execution_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving execution summary for {execution_id}: {str(e)}")
            return False

    def save_quality_report(self, report_id: str, report: Dict[str, Any]) -> bool:
        """
        Save quality report to storage

        Args:
            report_id: Unique identifier for the report
            report: Quality report data

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp to report
            report_with_timestamp = {
                **report,
                'timestamp': datetime.now().isoformat()
            }

            # Create file path
            file_path = os.path.join(self.storage_dir, f"quality_{report_id}.json")

            # Write to file
            with open(file_path, 'w') as f:
                json.dump(report_with_timestamp, f, indent=2)

            logger.info(f"Saved quality report for {report_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving quality report for {report_id}: {str(e)}")
            return False

    def get_execution_summary(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve execution summary from storage

        Args:
            execution_id: Unique identifier for the execution

        Returns:
            Execution summary data or None if not found
        """
        try:
            file_path = os.path.join(self.storage_dir, f"execution_{execution_id}.json")

            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error retrieving execution summary for {execution_id}: {str(e)}")
            return None

    def get_quality_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve quality report from storage

        Args:
            report_id: Unique identifier for the report

        Returns:
            Quality report data or None if not found
        """
        try:
            file_path = os.path.join(self.storage_dir, f"quality_{report_id}.json")

            if not os.path.exists(file_path):
                return None

            with open(file_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error retrieving quality report for {report_id}: {str(e)}")
            return None

    def list_execution_summaries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all execution summaries

        Args:
            limit: Maximum number of summaries to return

        Returns:
            List of execution summaries
        """
        try:
            summaries = []
            for filename in os.listdir(self.storage_dir):
                if filename.startswith("execution_") and filename.endswith(".json"):
                    file_path = os.path.join(self.storage_dir, filename)
                    with open(file_path, 'r') as f:
                        summary = json.load(f)
                        summaries.append(summary)

            # Sort by timestamp descending (most recent first)
            summaries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return summaries[:limit]

        except Exception as e:
            logger.error(f"Error listing execution summaries: {str(e)}")
            return []

    def list_quality_reports(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all quality reports

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of quality reports
        """
        try:
            reports = []
            for filename in os.listdir(self.storage_dir):
                if filename.startswith("quality_") and filename.endswith(".json"):
                    file_path = os.path.join(self.storage_dir, filename)
                    with open(file_path, 'r') as f:
                        report = json.load(f)
                        reports.append(report)

            # Sort by timestamp descending (most recent first)
            reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return reports[:limit]

        except Exception as e:
            logger.error(f"Error listing quality reports: {str(e)}")
            return []