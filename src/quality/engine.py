"""
Quality engine for Irish Energy Analytics Data Platform
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable, Optional, Union
from datetime import datetime
from loguru import logger
from .models import QualityRuleResult, QualityStatus, QualityReport, QualityRule


class QualityEngine:
    """
    Reusable quality engine that executes configurable sets of validation rules
    """

    def __init__(self):
        self.rules: List[QualityRule] = []

    def register_rule(self, rule: QualityRule) -> None:
        """Register a quality rule for execution"""
        self.rules.append(rule)

    def execute_rules(self, data: Union[pd.DataFrame, Dict[str, Any]],
                     dataset_name: str,
                     data_layer: str,
                     pipeline_date: str) -> QualityReport:
        """
        Execute all registered quality rules against the provided data

        Args:
            data: Data to validate (DataFrame or Dict)
            dataset_name: Name of the dataset being validated
            data_layer: Layer being validated (bronze, silver, gold)
            pipeline_date: Date of the pipeline run

        Returns:
            QualityReport: Complete quality assessment report
        """
        logger.info(f"Executing quality checks for {dataset_name} at {data_layer} layer")

        rule_results: List[QualityRuleResult] = []
        passed_checks = 0
        failed_checks = 0
        warning_checks = 0

        # Get data statistics for report
        total_records = self._get_record_count(data)

        # Execute each registered rule
        for rule in self.rules:
            try:
                # Execute the rule check function
                result = self._execute_single_rule(rule, data)
                rule_results.append(result)

                # Update counters based on result status
                if result.status == QualityStatus.PASS:
                    passed_checks += 1
                elif result.status == QualityStatus.FAIL:
                    failed_checks += 1
                elif result.status == QualityStatus.WARNING:
                    warning_checks += 1

            except Exception as e:
                logger.error(f"Error executing rule {rule['name']}: {str(e)}")
                rule_results.append(QualityRuleResult(
                    rule_name=rule['name'],
                    status=QualityStatus.FAIL,
                    message=f"Rule execution error: {str(e)}"
                ))
                failed_checks += 1

        # Calculate overall score
        total_checks = len(rule_results)
        if total_checks > 0:
            # Weighted scoring (simple average for now)
            score = self._calculate_score(rule_results)
        else:
            score = 100.0  # No checks = perfect score

        # Determine overall quality status
        quality_status = self._determine_quality_status(rule_results)

        # Create and return the quality report
        report = QualityReport(
            dataset_name=dataset_name,
            data_layer=data_layer,
            pipeline_date=pipeline_date,
            assessment_timestamp=datetime.utcnow(),
            total_records=total_records,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            warning_checks=warning_checks,
            overall_score=score,
            quality_status=quality_status,
            rule_results=rule_results
        )

        return report

    def _execute_single_rule(self, rule: QualityRule, data: Union[pd.DataFrame, Dict[str, Any]]) -> QualityRuleResult:
        """
        Execute a single quality rule

        Args:
            rule: Quality rule to execute
            data: Data to validate

        Returns:
            QualityRuleResult: Result of the rule execution
        """
        try:
            # Execute the rule function
            result = rule['check_function'](data)

            # Interpret the result
            if isinstance(result, tuple):
                # Assume (status, message, details) format
                status, message, details = result
            elif isinstance(result, bool):
                # Boolean result - True = PASS, False = FAIL
                status = QualityStatus.PASS if result else QualityStatus.FAIL
                message = None
                details = None
            else:
                # Default to PASS if unknown format
                status = QualityStatus.PASS
                message = None
                details = None

            return QualityRuleResult(
                rule_name=rule['name'],
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            logger.error(f"Exception in rule {rule['name']}: {str(e)}")
            return QualityRuleResult(
                rule_name=rule['name'],
                status=QualityStatus.FAIL,
                message=f"Rule execution error: {str(e)}"
            )

    def _get_record_count(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> int:
        """
        Get the count of records in the data

        Args:
            data: Data to count records for

        Returns:
            int: Number of records
        """
        if isinstance(data, pd.DataFrame):
            return len(data)
        elif isinstance(data, dict):
            # For dictionaries, try to count elements
            if 'records' in data:
                return len(data['records'])
            elif 'data' in data:
                return len(data['data'])
            else:
                # Estimate based on length of data
                return len(str(data)) if data else 0
        else:
            return 0

    def _calculate_score(self, rule_results: List[QualityRuleResult]) -> float:
        """
        Calculate weighted quality score based on rule results

        Args:
            rule_results: List of rule execution results

        Returns:
            float: Quality score between 0 and 100
        """
        if not rule_results:
            return 100.0

        # For simplicity, we'll calculate score as percentage of passed rules
        passed = sum(1 for r in rule_results if r.status == QualityStatus.PASS)
        failed = sum(1 for r in rule_results if r.status == QualityStatus.FAIL)
        warning = sum(1 for r in rule_results if r.status == QualityStatus.WARNING)

        # Simple scoring: 100 * (passed / total)
        total = len(rule_results)
        if total == 0:
            return 100.0

        # Weight failures more heavily than warnings
        score = 100.0 * (passed / total)

        # Apply penalties for warnings and failures
        penalty = (failed * 2.0) + (warning * 0.5)  # Weight failures more heavily
        score = max(0.0, score - penalty)

        return round(score, 2)

    def _determine_quality_status(self, rule_results: List[QualityRuleResult]) -> QualityStatus:
        """
        Determine overall quality status based on rule results

        Args:
            rule_results: List of rule execution results

        Returns:
            QualityStatus: Overall quality status
        """
        if not rule_results:
            return QualityStatus.PASS

        # If any critical failures, return FAIL
        critical_failures = [r for r in rule_results if r.status == QualityStatus.FAIL]
        if critical_failures:
            return QualityStatus.FAIL

        # If any warnings, return WARNING
        warnings = [r for r in rule_results if r.status == QualityStatus.WARNING]
        if warnings:
            return QualityStatus.WARNING

        # Otherwise, return PASS
        return QualityStatus.PASS