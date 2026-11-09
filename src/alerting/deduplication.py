"""
Alert deduplication and suppression for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from src.alerting.models import Alert, Incident, AlertSeverity, AlertStatus
from src.alerting.engine import AlertEvaluationEngine


class AlertDeduplicator:
    """
    Handles deduplication and suppression of alerts
    """

    def __init__(self, suppression_window_minutes: int = 60):
        self.suppression_window_minutes = suppression_window_minutes
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_suppression_history: List[Dict[str, Any]] = []

    def should_suppress_alert(self, alert: Alert) -> bool:
        """
        Determine if an alert should be suppressed due to deduplication

        Args:
            alert: Alert to evaluate

        Returns:
            True if alert should be suppressed, False otherwise
        """
        # Check if we have a similar alert active within suppression window
        current_time = datetime.now()

        # Look for similar alerts in active alerts
        for existing_alert_id, existing_alert in self.active_alerts.items():
            # If it's the same alert, don't suppress
            if existing_alert_id == alert.alert_id:
                continue

            # Check if it's the same rule and category
            if (existing_alert.rule_id == alert.rule_id and
                existing_alert.category == alert.category):

                # Check if it's within suppression window
                time_diff = current_time - existing_alert.detection_timestamp
                if time_diff <= timedelta(minutes=self.suppression_window_minutes):
                    # Suppress this alert - it's a duplicate
                    suppression_info = {
                        'suppressed_alert_id': alert.alert_id,
                        'original_alert_id': existing_alert.alert_id,
                        'suppression_reason': 'duplicate_alert',
                        'timestamp': current_time
                    }
                    self.alert_suppression_history.append(suppression_info)
                    logger.debug(f"Suppressing duplicate alert {alert.alert_id} from {existing_alert.alert_id}")
                    return True

        return False

    def register_alert(self, alert: Alert):
        """
        Register an alert as active (for deduplication purposes)

        Args:
            alert: Alert to register
        """
        self.active_alerts[alert.alert_id] = alert

        # Remove old alerts that are beyond the suppression window
        current_time = datetime.now()
        expired_alerts = []
        for alert_id, alert_obj in self.active_alerts.items():
            time_diff = current_time - alert_obj.detection_timestamp
            if time_diff > timedelta(minutes=self.suppression_window_minutes):
                expired_alerts.append(alert_id)

        for alert_id in expired_alerts:
            del self.active_alerts[alert_id]

    def clear_suppressions(self):
        """Clear all active alerts and suppression history"""
        self.active_alerts.clear()
        self.alert_suppression_history.clear()

    def get_suppression_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent suppression history

        Args:
            limit: Maximum number of suppression events to return

        Returns:
            List of suppression events
        """
        return self.alert_suppression_history[-limit:] if self.alert_suppression_history else []