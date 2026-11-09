"""
Alert rules for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
from src.alerting.models import AlertRule, AlertCategory, AlertSeverity
from src.observability.models import DatasetFreshnessMetrics, QualityMetrics
from src.quality.models import QualityReport, QualityStatus
from src.monitoring.service import MonitoringService


class AlertRules:
    """Collection of alert rules for the platform"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self._initialize_rules()

    def _initialize_rules(self):
        """Initialize all alert rules"""
        # Pipeline failure rules
        self.rules.extend([
            self._create_pipeline_failure_rule(),
            self._create_stage_failure_rule(),
            self._create_repeated_failure_rule()
        ])

        # Ingestion problem rules
        self.rules.extend([
            self._create_ingestion_failure_rule("EirGrid"),
            self._create_ingestion_failure_rule("OpenMeteo"),
            self._create_missing_data_rule()
        ])

        # Data freshness rules
        self.rules.extend([
            self._create_freshness_delayed_rule(),
            self._create_freshness_stale_rule(),
            self._create_missing_partition_rule()
        ])

        # Data quality rules
        self.rules.extend([
            self._create_quality_threshold_rule(),
            self._create_critical_quality_rule(),
            self._create_rejected_records_rule()
        ])

        # Performance rules
        self.rules.extend([
            self._create_pipeline_duration_rule(),
            self._create_stage_duration_rule()
        ])

    def _create_pipeline_failure_rule(self) -> AlertRule:
        """Create rule for pipeline execution failures"""
        def evaluate_pipeline_failure(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would be called with event data from orchestration
            # For now, we just return a basic structure
            return {
                'category': AlertCategory.PIPELINE_FAILURE,
                'severity': AlertSeverity.CRITICAL,
                'title': 'Pipeline Execution Failed',
                'description': 'The entire pipeline execution failed',
                'threshold': None,
                'evidence': 'Pipeline execution failed with error: ' + str(event_data.get('error_message', 'Unknown'))
            }

        return {
            'rule_id': 'pipeline_failure',
            'category': AlertCategory.PIPELINE_FAILURE,
            'severity': AlertSeverity.CRITICAL,
            'title': 'Pipeline Execution Failed',
            'description': 'The entire pipeline execution failed',
            'enabled': True,
            'threshold': None,
            'window_minutes': 0,
            'evaluation_function': evaluate_pipeline_failure
        }

    def _create_stage_failure_rule(self) -> AlertRule:
        """Create rule for individual stage failures"""
        def evaluate_stage_failure(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            return {
                'category': AlertCategory.PIPELINE_FAILURE,
                'severity': AlertSeverity.ERROR,
                'title': 'Pipeline Stage Failed',
                'description': 'An individual pipeline stage failed',
                'threshold': None,
                'evidence': f'Stage {event_data.get("stage_name", "unknown")} failed with error: ' +
                           str(event_data.get('error_message', 'Unknown'))
            }

        return {
            'rule_id': 'stage_failure',
            'category': AlertCategory.PIPELINE_FAILURE,
            'severity': AlertSeverity.ERROR,
            'title': 'Pipeline Stage Failed',
            'description': 'An individual pipeline stage failed',
            'enabled': True,
            'threshold': None,
            'window_minutes': 0,
            'evaluation_function': evaluate_stage_failure
        }

    def _create_repeated_failure_rule(self) -> AlertRule:
        """Create rule for repeated execution failures"""
        def evaluate_repeated_failure(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            return {
                'category': AlertCategory.PIPELINE_FAILURE,
                'severity': AlertSeverity.WARNING,
                'title': 'Repeated Pipeline Failures',
                'description': 'Multiple consecutive pipeline executions have failed',
                'threshold': 3,
                'evidence': 'Detected 3 consecutive failures for execution: ' + str(event_data.get('execution_id', 'unknown'))
            }

        return {
            'rule_id': 'repeated_failure',
            'category': AlertCategory.PIPELINE_FAILURE,
            'severity': AlertSeverity.WARNING,
            'title': 'Repeated Pipeline Failures',
            'description': 'Multiple consecutive pipeline executions have failed',
            'enabled': True,
            'threshold': 3,
            'window_minutes': 1440,  # 24 hours
            'evaluation_function': evaluate_repeated_failure
        }

    def _create_ingestion_failure_rule(self, source: str) -> AlertRule:
        """Create rule for ingestion failures"""
        def evaluate_ingestion_failure(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            return {
                'category': AlertCategory.INGESTION_PROBLEM,
                'severity': AlertSeverity.CRITICAL,
                'title': f'{source} Ingestion Failed',
                'description': f'{source} data ingestion failed',
                'threshold': None,
                'evidence': f'{source} ingestion failed with error: ' + str(event_data.get('error_message', 'Unknown'))
            }

        return {
            'rule_id': f'ingestion_failure_{source.lower()}',
            'category': AlertCategory.INGESTION_PROBLEM,
            'severity': AlertSeverity.CRITICAL,
            'title': f'{source} Ingestion Failed',
            'description': f'{source} data ingestion failed',
            'enabled': True,
            'threshold': None,
            'window_minutes': 0,
            'evaluation_function': evaluate_ingestion_failure
        }

    def _create_missing_data_rule(self) -> AlertRule:
        """Create rule for missing expected data"""
        def evaluate_missing_data(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            return {
                'category': AlertCategory.INGESTION_PROBLEM,
                'severity': AlertSeverity.WARNING,
                'title': 'Expected Data Missing',
                'description': 'Expected data for the pipeline date was not received',
                'threshold': None,
                'evidence': 'Expected data for date ' + str(event_data.get('pipeline_date', 'unknown')) + ' was not found'
            }

        return {
            'rule_id': 'missing_data',
            'category': AlertCategory.INGESTION_PROBLEM,
            'severity': AlertSeverity.WARNING,
            'title': 'Expected Data Missing',
            'description': 'Expected data for the pipeline date was not received',
            'enabled': True,
            'threshold': None,
            'window_minutes': 0,
            'evaluation_function': evaluate_missing_data
        }

    def _create_freshness_delayed_rule(self) -> AlertRule:
        """Create rule for delayed data freshness"""
        def evaluate_freshness_delayed(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would check DatasetFreshnessMetrics from observability
            freshness_metrics = event_data.get('freshness_metrics')
            if freshness_metrics and freshness_metrics.get('freshness_status') == 'DELAYED':
                return {
                    'category': AlertCategory.DATA_FRESHNESS,
                    'severity': AlertSeverity.WARNING,
                    'title': 'Data Delayed',
                    'description': 'Data freshness is delayed beyond threshold',
                    'threshold': freshness_metrics.get('freshness_threshold_days'),
                    'evidence': f'Dataset {freshness_metrics.get("dataset_name")} is delayed by {freshness_metrics.get("data_age_days")} days'
                }
            return None

        return {
            'rule_id': 'freshness_delayed',
            'category': AlertCategory.DATA_FRESHNESS,
            'severity': AlertSeverity.WARNING,
            'title': 'Data Delayed',
            'description': 'Data freshness is delayed beyond threshold',
            'enabled': True,
            'threshold': 2,
            'window_minutes': 0,
            'evaluation_function': evaluate_freshness_delayed
        }

    def _create_freshness_stale_rule(self) -> AlertRule:
        """Create rule for stale data freshness"""
        def evaluate_freshness_stale(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would check DatasetFreshnessMetrics from observability
            freshness_metrics = event_data.get('freshness_metrics')
            if freshness_metrics and freshness_metrics.get('freshness_status') == 'STALE':
                return {
                    'category': AlertCategory.DATA_FRESHNESS,
                    'severity': AlertSeverity.ERROR,
                    'title': 'Data Stale',
                    'description': 'Data freshness is stale beyond threshold',
                    'threshold': freshness_metrics.get('freshness_threshold_days'),
                    'evidence': f'Dataset {freshness_metrics.get("dataset_name")} is stale by {freshness_metrics.get("data_age_days")} days'
                }
            return None

        return {
            'rule_id': 'freshness_stale',
            'category': AlertCategory.DATA_FRESHNESS,
            'severity': AlertSeverity.ERROR,
            'title': 'Data Stale',
            'description': 'Data freshness is stale beyond threshold',
            'enabled': True,
            'threshold': 3,
            'window_minutes': 0,
            'evaluation_function': evaluate_freshness_stale
        }

    def _create_missing_partition_rule(self) -> AlertRule:
        """Create rule for missing data partitions"""
        def evaluate_missing_partition(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            return {
                'category': AlertCategory.DATA_FRESHNESS,
                'severity': AlertSeverity.ERROR,
                'title': 'Missing Data Partition',
                'description': 'Expected data partition is missing',
                'threshold': None,
                'evidence': 'Partition for date ' + str(event_data.get('partition_date', 'unknown')) + ' is missing'
            }

        return {
            'rule_id': 'missing_partition',
            'category': AlertCategory.DATA_FRESHNESS,
            'severity': AlertSeverity.ERROR,
            'title': 'Missing Data Partition',
            'description': 'Expected data partition is missing',
            'enabled': True,
            'threshold': None,
            'window_minutes': 0,
            'evaluation_function': evaluate_missing_partition
        }

    def _create_quality_threshold_rule(self) -> AlertRule:
        """Create rule for quality score below threshold"""
        def evaluate_quality_threshold(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would check QualityMetrics from observability
            quality_metrics = event_data.get('quality_metrics')
            if quality_metrics and quality_metrics.get('overall_score', 1.0) < 0.95:
                return {
                    'category': AlertCategory.DATA_QUALITY,
                    'severity': AlertSeverity.WARNING,
                    'title': 'Quality Score Below Threshold',
                    'description': 'Data quality score dropped below acceptable threshold',
                    'threshold': 0.95,
                    'evidence': f'Quality score {quality_metrics.get("overall_score")} below threshold 0.95 for dataset {quality_metrics.get("dataset_name")}'
                }
            return None

        return {
            'rule_id': 'quality_threshold',
            'category': AlertCategory.DATA_QUALITY,
            'severity': AlertSeverity.WARNING,
            'title': 'Quality Score Below Threshold',
            'description': 'Data quality score dropped below acceptable threshold',
            'enabled': True,
            'threshold': 0.95,
            'window_minutes': 0,
            'evaluation_function': evaluate_quality_threshold
        }

    def _create_critical_quality_rule(self) -> AlertRule:
        """Create rule for critical quality rule failures"""
        def evaluate_critical_quality(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would check QualityReport from quality framework
            quality_report = event_data.get('quality_report')
            if quality_report and quality_report.get('quality_status') == 'FAIL':
                failed_rules = [r for r in quality_report.get('rule_results', [])
                              if r.get('status') == 'FAIL']
                return {
                    'category': AlertCategory.DATA_QUALITY,
                    'severity': AlertSeverity.CRITICAL,
                    'title': 'Critical Quality Rule Failed',
                    'description': 'A critical quality rule has failed',
                    'threshold': None,
                    'evidence': f'Critical quality rule failed for dataset {quality_report.get("dataset_name")}. Failed rules: {[r.get("rule_name") for r in failed_rules]}'
                }
            return None

        return {
            'rule_id': 'critical_quality',
            'category': AlertCategory.DATA_QUALITY,
            'severity': AlertSeverity.CRITICAL,
            'title': 'Critical Quality Rule Failed',
            'description': 'A critical quality rule has failed',
            'enabled': True,
            'threshold': None,
            'window_minutes': 0,
            'evaluation_function': evaluate_critical_quality
        }

    def _create_rejected_records_rule(self) -> AlertRule:
        """Create rule for excessive rejected records"""
        def evaluate_rejected_records(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would check quality metrics
            quality_metrics = event_data.get('quality_metrics')
            if quality_metrics and quality_metrics.get('failed_checks', 0) > 0:
                # Calculate percentage of rejected records
                total = quality_metrics.get('total_records', 1)
                failed = quality_metrics.get('failed_checks', 0)
                rejection_percentage = (failed / total) * 100

                if rejection_percentage > 5:  # 5% threshold
                    return {
                        'category': AlertCategory.DATA_QUALITY,
                        'severity': AlertSeverity.WARNING,
                        'title': 'Excessive Rejected Records',
                        'description': 'Too many records were rejected during processing',
                        'threshold': 5,
                        'evidence': f'{rejection_percentage:.1f}% of records rejected for dataset {quality_metrics.get("dataset_name")}'
                    }
            return None

        return {
            'rule_id': 'rejected_records',
            'category': AlertCategory.DATA_QUALITY,
            'severity': AlertSeverity.WARNING,
            'title': 'Excessive Rejected Records',
            'description': 'Too many records were rejected during processing',
            'enabled': True,
            'threshold': 5,
            'window_minutes': 0,
            'evaluation_function': evaluate_rejected_records
        }

    def _create_pipeline_duration_rule(self) -> AlertRule:
        """Create rule for pipeline execution exceeding duration threshold"""
        def evaluate_pipeline_duration(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would check pipeline execution metrics
            pipeline_metrics = event_data.get('pipeline_metrics')
            if pipeline_metrics and pipeline_metrics.get('duration_seconds', 0) > 3600:  # 1 hour threshold
                return {
                    'category': AlertCategory.PERFORMANCE,
                    'severity': AlertSeverity.WARNING,
                    'title': 'Pipeline Execution Too Long',
                    'description': 'Pipeline execution exceeded expected duration',
                    'threshold': 3600,
                    'evidence': f'Pipeline execution took {pipeline_metrics.get("duration_seconds")} seconds, exceeding threshold of 3600 seconds'
                }
            return None

        return {
            'rule_id': 'pipeline_duration',
            'category': AlertCategory.PERFORMANCE,
            'severity': AlertSeverity.WARNING,
            'title': 'Pipeline Execution Too Long',
            'description': 'Pipeline execution exceeded expected duration',
            'enabled': True,
            'threshold': 3600,
            'window_minutes': 0,
            'evaluation_function': evaluate_pipeline_duration
        }

    def _create_stage_duration_rule(self) -> AlertRule:
        """Create rule for stage execution exceeding duration threshold"""
        def evaluate_stage_duration(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            # This would check stage execution metrics
            stage_metrics = event_data.get('stage_metrics')
            if stage_metrics and stage_metrics.get('duration_seconds', 0) > 600:  # 10 minutes threshold
                return {
                    'category': AlertCategory.PERFORMANCE,
                    'severity': AlertSeverity.WARNING,
                    'title': 'Stage Execution Too Long',
                    'description': 'Stage execution exceeded expected duration',
                    'threshold': 600,
                    'evidence': f'Stage {stage_metrics.get("stage_name")} took {stage_metrics.get("duration_seconds")} seconds, exceeding threshold of 600 seconds'
                }
            return None

        return {
            'rule_id': 'stage_duration',
            'category': AlertCategory.PERFORMANCE,
            'severity': AlertSeverity.WARNING,
            'title': 'Stage Execution Too Long',
            'description': 'Stage execution exceeded expected duration',
            'enabled': True,
            'threshold': 600,
            'window_minutes': 0,
            'evaluation_function': evaluate_stage_duration
        }

    def get_enabled_rules(self) -> List[AlertRule]:
        """Get all enabled alert rules"""
        return [rule for rule in self.rules if rule['enabled']]

    def get_rules_by_category(self, category: AlertCategory) -> List[AlertRule]:
        """Get all rules of a specific category"""
        return [rule for rule in self.rules if rule['category'] == category]