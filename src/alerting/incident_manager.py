"""
Incident management for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
from loguru import logger
from src.alerting.models import Incident, IncidentStatus, AlertSeverity
from src.alerting.engine import AlertEvaluationEngine


class IncidentManager:
    """
    Manages the lifecycle of incidents from creation to resolution
    """

    def __init__(self, alert_engine: AlertEvaluationEngine = None):
        self.alert_engine = alert_engine or AlertEvaluationEngine()
        self.incidents: Dict[str, Incident] = {}
        self.incident_history: List[Incident] = []

    def create_incident(self, alert_ids: List[str], title: str, description: str,
                       severity: AlertSeverity, affected_datasets: List[str],
                       execution_id: Optional[str] = None) -> Incident:
        """
        Create a new incident from one or more alerts

        Args:
            alert_ids: List of alert IDs associated with this incident
            title: Incident title
            description: Incident description
            severity: Severity level
            affected_datasets: List of affected datasets
            execution_id: Associated execution ID

        Returns:
            Created incident
        """
        incident_id = f"inc_{uuid4().hex[:8]}"

        incident = Incident(
            incident_id=incident_id,
            alert_ids=alert_ids,
            title=title,
            description=description,
            severity=severity,
            affected_datasets=affected_datasets,
            execution_id=execution_id,
            creation_timestamp=datetime.now(),
            last_updated_timestamp=datetime.now(),
            resolution_timestamp=None,
            status=IncidentStatus.OPEN,
            history=[{
                'timestamp': datetime.now(),
                'action': 'created',
                'details': f'Incident created from alerts: {alert_ids}'
            }]
        )

        self.incidents[incident_id] = incident
        self.incident_history.append(incident)

        logger.info(f"Created incident {incident_id} for alerts: {alert_ids}")
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """
        Retrieve an incident by ID

        Args:
            incident_id: Incident identifier

        Returns:
            Incident or None if not found
        """
        return self.incidents.get(incident_id)

    def acknowledge_incident(self, incident_id: str, notes: Optional[str] = None) -> bool:
        """
        Acknowledge an incident (mark as being worked on)

        Args:
            incident_id: Incident identifier
            notes: Additional notes about acknowledgment

        Returns:
            True if successful, False otherwise
        """
        incident = self.incidents.get(incident_id)
        if not incident:
            return False

        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.last_updated_timestamp = datetime.now()

        # Add to history
        history_entry = {
            'timestamp': datetime.now(),
            'action': 'acknowledged',
            'details': notes or 'Incident acknowledged'
        }
        incident.history.append(history_entry)

        logger.info(f"Acknowledged incident {incident_id}")
        return True

    def resolve_incident(self, incident_id: str, resolution_notes: Optional[str] = None) -> bool:
        """
        Resolve an incident

        Args:
            incident_id: Incident identifier
            resolution_notes: Notes about resolution

        Returns:
            True if successful, False otherwise
        """
        incident = self.incidents.get(incident_id)
        if not incident:
            return False

        incident.status = IncidentStatus.RESOLVED
        incident.resolution_timestamp = datetime.now()
        incident.last_updated_timestamp = datetime.now()

        # Add to history
        history_entry = {
            'timestamp': datetime.now(),
            'action': 'resolved',
            'details': resolution_notes or 'Incident resolved'
        }
        incident.history.append(history_entry)

        logger.info(f"Resolved incident {incident_id}")
        return True

    def get_open_incidents(self) -> List[Incident]:
        """
        Get all currently open incidents

        Returns:
            List of open incidents
        """
        return [incident for incident in self.incidents.values()
                if incident.status == IncidentStatus.OPEN]

    def get_incident_history(self, limit: int = 100) -> List[Incident]:
        """
        Get recent incident history

        Args:
            limit: Maximum number of incidents to return

        Returns:
            List of recent incidents
        """
        return self.incident_history[-limit:] if self.incident_history else []

    def get_incidents_by_severity(self, severity: AlertSeverity) -> List[Incident]:
        """
        Get incidents filtered by severity

        Args:
            severity: Severity level to filter by

        Returns:
            List of incidents matching severity
        """
        return [incident for incident in self.incidents.values()
                if incident.severity == severity]

    def get_incidents_by_dataset(self, dataset_name: str) -> List[Incident]:
        """
        Get incidents affecting a specific dataset

        Args:
            dataset_name: Name of dataset to filter by

        Returns:
            List of incidents affecting the dataset
        """
        return [incident for incident in self.incidents.values()
                if dataset_name in incident.affected_datasets]

    def clear_incidents(self):
        """Clear all incidents"""
        self.incidents.clear()
        self.incident_history.clear()