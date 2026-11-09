"""
Alert evaluation engine for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
from src.alerting.models import Alert, AlertEvent, AlertRule, AlertSeverity, AlertCategory, AlertStatus
from src.alerting.rules import AlertRules
from src.observability.models import PipelineExecutionMetrics, StageMetrics, DatasetFreshnessMetrics, QualityMetrics
from src.quality.models import QualityReport


class AlertEvaluationEngine:
    """
    Evaluates operational events against alert rules to generate alerts
    """

    def __init__(self, alert_rules: AlertRules = None):
        self.alert_rules = alert_rules or AlertRules()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

    def evaluate_event(self, event_data: Dict[str, Any]) -> List[AlertEvent]:
        """
        Evaluate an event against all applicable alert rules

        Args:
            event_data: Dictionary containing event data

        Returns:
            List of AlertEvents that were triggered
        """
        alert_events = []

        # Get all enabled rules
        enabled_rules = self.alert_rules.get_enabled_rules()

        # Evaluate each rule against the event
        for rule in enabled_rules:
            try:
                # Skip rules that don't match the event type
                if not self._should_evaluate_rule(rule, event_data):
                    continue

                # Evaluate the rule
                result = rule['evaluation_function'](event_data)

                if result:
                    # Create an alert event
                    alert_event = self._create_alert_event(rule, event_data, result)
                    alert_events.append(alert_event)

            except Exception as e:
                logger.error(f"Error evaluating rule {rule['rule_id']}: {str(e)}")

        return alert_events

    def _should_evaluate_rule(self, rule: AlertRule, event_data: Dict[str, Any]) -> bool:
        """
        Determine if a rule should be evaluated for the given event

        Args:
            rule: Alert rule to evaluate
            event_data: Event data

        Returns:
            True if rule should be evaluated, False otherwise
        """
        # Basic categorization logic - in a real implementation, this would be more sophisticated
        category = rule['category']

        # Check if event matches rule category
        if category == AlertCategory.PIPELINE_FAILURE:
            return 'execution_id' in event_data or 'error_message' in event_data

        elif category == AlertCategory.INGESTION_PROBLEM:
            return 'source' in event_data or 'error_message' in event_data

        elif category == AlertCategory.DATA_FRESHNESS:
            return 'freshness_metrics' in event_data or 'partition_date' in event_data

        elif category == AlertCategory.DATA_QUALITY:
            return 'quality_metrics' in event_data or 'quality_report' in event_data

        elif category == AlertCategory.PERFORMANCE:
            return 'pipeline_metrics' in event_data or 'stage_metrics' in event_data

        return True  # Default to evaluating if no specific logic

    def _create_alert_event(self, rule: AlertRule, event_data: Dict[str, Any],
                          evaluation_result: Dict[str, Any]) -> AlertEvent:
        """
        Create an alert event from rule evaluation result

        Args:
            rule: The rule that triggered
            event_data: Original event data
            evaluation_result: Result from rule evaluation

        Returns:
            AlertEvent object
        """
        return {
            'alert_id': f"alert_{rule['rule_id']}_{int(datetime.now().timestamp())}",
            'rule_id': rule['rule_id'],
            'category': evaluation_result.get('category', rule['category']),
            'severity': evaluation_result.get('severity', rule['severity']),
            'affected_dataset': event_data.get('dataset_name'),
            'execution_id': event_data.get('execution_id'),
            'timestamp': datetime.now(),
            'metric_values': event_data.get('metric_values'),
            'evidence': evaluation_result.get('evidence', '')
        }

    def process_alert_events(self, alert_events: List[AlertEvent]) -> List[Alert]:
        """
        Process alert events and create alerts

        Args:
            alert_events: List of alert events to process

        Returns:
            List of generated alerts
        """
        alerts = []

        for event in alert_events:
            # Create alert from event
            alert = self._create_alert_from_event(event)
            alerts.append(alert)

            # Store in active alerts
            self.active_alerts[alert.alert_id] = alert

            # Add to history
            self.alert_history.append(alert)

        return alerts

    def _create_alert_from_event(self, event: AlertEvent) -> Alert:
        """
        Create an alert from an alert event

        Args:
            event: Alert event to convert

        Returns:
            Alert object
        """
        return Alert(
            alert_id=event['alert_id'],
            rule_id=event['rule_id'],
            category=event['category'],
            severity=event['severity'],
            title=event['evidence'][:100] + "..." if len(event['evidence']) > 100 else event['evidence'],
            description=event['evidence'],
            affected_dataset=event['affected_dataset'],
            execution_id=event['execution_id'],
            detection_timestamp=event['timestamp'],
            metric_values=event['metric_values'],
            threshold=None,  # Would be set from rule
            status=AlertStatus.ACTIVE,
            evidence=event['evidence']
        )

    def get_active_alerts(self) -> Dict[str, Alert]:
        """
        Get all currently active alerts

        Returns:
            Dictionary of active alerts by alert_id
        """
        return self.active_alerts.copy()

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get recent alert history

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        return self.alert_history[-limit:] if self.alert_history else []

    def clear_alerts(self):
        """Clear all active alerts"""
        self.active_alerts.clear()
        self.alert_history.clear()