"""
Main alerting service for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from src.alerting.models import Alert, Incident, AlertSeverity
from src.alerting.engine import AlertEvaluationEngine
from src.alerting.incident_manager import IncidentManager
from src.alerting.notification import NotificationProvider, MockNotificationProvider
from src.alerting.deduplication import AlertDeduplicator
from src.monitoring.service import MonitoringService


class AlertingService:
    """
    Main alerting service that coordinates all alerting components
    """

    def __init__(self, notification_provider: NotificationProvider = None):
        self.alert_engine = AlertEvaluationEngine()
        self.incident_manager = IncidentManager(self.alert_engine)
        self.deduplicator = AlertDeduplicator()
        self.notification_provider = notification_provider or MockNotificationProvider()

        # Track alerts that have been processed
        self.processed_alerts: Dict[str, Alert] = {}

    def process_event(self, event_data: Dict[str, Any]) -> List[Alert]:
        """
        Process an event and generate alerts if appropriate

        Args:
            event_data: Event data to process

        Returns:
            List of generated alerts
        """
        logger.info(f"Processing event: {event_data.get('event_type', 'unknown')}")

        # Evaluate event against alert rules
        alert_events = self.alert_engine.evaluate_event(event_data)

        # Process alert events
        alerts = self.alert_engine.process_alert_events(alert_events)

        # Apply deduplication
        filtered_alerts = []
        for alert in alerts:
            if not self.deduplicator.should_suppress_alert(alert):
                # Register alert for future deduplication
                self.deduplicator.register_alert(alert)
                filtered_alerts.append(alert)
            else:
                logger.debug(f"Skipping duplicate alert: {alert.alert_id}")

        # Create incidents for new alerts
        for alert in filtered_alerts:
            self._create_incident_for_alert(alert)

        # Store processed alerts
        for alert in filtered_alerts:
            self.processed_alerts[alert.alert_id] = alert

        return filtered_alerts

    def _create_incident_for_alert(self, alert: Alert) -> Optional[Incident]:
        """
        Create an incident for a new alert

        Args:
            alert: Alert to create incident for

        Returns:
            Created incident or None if failed
        """
        try:
            # Create incident from alert
            incident = self.incident_manager.create_incident(
                alert_ids=[alert.alert_id],
                title=alert.title,
                description=alert.description,
                severity=alert.severity,
                affected_datasets=[alert.affected_dataset] if alert.affected_dataset else [],
                execution_id=alert.execution_id
            )

            # Send notification
            self._send_notification(incident)

            return incident

        except Exception as e:
            logger.error(f"Error creating incident for alert {alert.alert_id}: {str(e)}")
            return None

    def _send_notification(self, incident: Incident):
        """
        Send notification for an incident

        Args:
            incident: Incident to notify about
        """
        try:
            # Convert incident to notification format
            notification_data = {
                'incident_id': incident.incident_id,
                'title': incident.title,
                'description': incident.description,
                'severity': incident.severity.value,
                'affected_datasets': incident.affected_datasets,
                'execution_id': incident.execution_id,
                'creation_timestamp': incident.creation_timestamp.isoformat(),
                'status': incident.status.value
            }

            # Send notification
            success = self.notification_provider.send_notification(notification_data)
            if success:
                logger.info(f"Notification sent for incident {incident.incident_id}")
            else:
                logger.error(f"Failed to send notification for incident {incident.incident_id}")

        except Exception as e:
            logger.error(f"Error sending notification for incident {incident.incident_id}: {str(e)}")

    def get_active_alerts(self) -> Dict[str, Alert]:
        """
        Get all currently active alerts

        Returns:
            Dictionary of active alerts
        """
        return self.alert_engine.get_active_alerts()

    def get_open_incidents(self) -> List[Incident]:
        """
        Get all currently open incidents

        Returns:
            List of open incidents
        """
        return self.incident_manager.get_open_incidents()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """
        Get a specific incident by ID

        Args:
            incident_id: Incident identifier

        Returns:
            Incident or None if not found
        """
        return self.incident_manager.get_incident(incident_id)

    def acknowledge_incident(self, incident_id: str, notes: Optional[str] = None) -> bool:
        """
        Acknowledge an incident

        Args:
            incident_id: Incident identifier
            notes: Notes about acknowledgment

        Returns:
            True if successful, False otherwise
        """
        return self.incident_manager.acknowledge_incident(incident_id, notes)

    def resolve_incident(self, incident_id: str, resolution_notes: Optional[str] = None) -> bool:
        """
        Resolve an incident

        Args:
            incident_id: Incident identifier
            resolution_notes: Notes about resolution

        Returns:
            True if successful, False otherwise
        """
        success = self.incident_manager.resolve_incident(incident_id, resolution_notes)
        if success:
            # In a real implementation, we'd send a resolution notification
            logger.info(f"Resolved incident {incident_id}")
        return success

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """
        Get recent alert history

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        return self.alert_engine.get_alert_history(limit)

    def get_incident_history(self, limit: int = 100) -> List[Incident]:
        """
        Get recent incident history

        Args:
            limit: Maximum number of incidents to return

        Returns:
            List of recent incidents
        """
        return self.incident_manager.get_incident_history(limit)

    def get_suppression_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent suppression history

        Args:
            limit: Maximum number of suppression events to return

        Returns:
            List of suppression events
        """
        return self.deduplicator.get_suppression_history(limit)

    def clear_all_data(self):
        """Clear all internal data structures"""
        self.alert_engine.clear_alerts()
        self.incident_manager.clear_incidents()
        self.deduplicator.clear_suppressions()
        self.processed_alerts.clear()