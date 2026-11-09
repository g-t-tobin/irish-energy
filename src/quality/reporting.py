"""
Quality reporting for Irish Energy Analytics Data Platform
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from .models import QualityReport


class QualityReporter:
    """
    Handles quality report generation and serialization
    """

    @staticmethod
    def to_json(report: QualityReport, pretty_print: bool = True) -> str:
        """
        Convert quality report to JSON string

        Args:
            report: QualityReport to convert
            pretty_print: Whether to format JSON nicely

        Returns:
            str: JSON representation of the report
        """
        report_dict = report.to_dict()

        if pretty_print:
            return json.dumps(report_dict, indent=2, default=str)
        else:
            return json.dumps(report_dict, default=str)

    @staticmethod
    def to_dict(report: QualityReport) -> Dict[str, Any]:
        """
        Convert quality report to dictionary

        Args:
            report: QualityReport to convert

        Returns:
            Dict: Dictionary representation of the report
        """
        return report.to_dict()

    @staticmethod
    def to_csv(report: QualityReport) -> str:
        """
        Convert quality report to CSV format (simplified)

        Args:
            report: QualityReport to convert

        Returns:
            str: CSV representation of the report
        """
        report_dict = report.to_dict()

        # Simplified CSV - just basic info
        csv_lines = [
            "metric,value",
            f"dataset_name,{report_dict['dataset_name']}",
            f"data_layer,{report_dict['data_layer']}",
            f"pipeline_date,{report_dict['pipeline_date']}",
            f"assessment_timestamp,{report_dict['assessment_timestamp']}",
            f"total_records,{report_dict['total_records']}",
            f"passed_checks,{report_dict['passed_checks']}",
            f"failed_checks,{report_dict['failed_checks']}",
            f"warning_checks,{report_dict['warning_checks']}",
            f"overall_score,{report_dict['overall_score']}",
            f"quality_status,{report_dict['quality_status']}"
        ]

        return '\n'.join(csv_lines)

    @staticmethod
    def get_summary(report: QualityReport) -> Dict[str, Any]:
        """
        Get a summary of the quality report

        Args:
            report: QualityReport to summarize

        Returns:
            Dict: Summary information
        """
        return {
            'dataset_name': report.dataset_name,
            'data_layer': report.data_layer,
            'pipeline_date': report.pipeline_date,
            'overall_score': report.overall_score,
            'quality_status': report.quality_status.value,
            'total_checks': len(report.rule_results),
            'passed_checks': report.passed_checks,
            'failed_checks': report.failed_checks,
            'warning_checks': report.warning_checks,
            'assessment_timestamp': report.assessment_timestamp.isoformat()
        }