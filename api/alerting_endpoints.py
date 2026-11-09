"""
Alerting API endpoints for Irish Energy Analytics Data Platform
"""
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from src.alerting.service import AlertingService
from src.alerting.models import Alert, Incident
from src.monitoring.service import MonitoringService


# Initialize the alerting service
alerting_service = AlertingService()


def get_alerting_service() -> AlertingService:
    """Dependency injection for alerting service"""
    return alerting_service


def get_monitoring_service() -> MonitoringService:
    """Dependency injection for monitoring service"""
    return MonitoringService()


# Define the API routes for alerting functionality
# Note: This will be mounted under /alerts in main.py
app = FastAPI(title="Alerting API", version="1.0.0")


@app.get("/health", response_model=dict)
async def alerting_health_check():
    """Health check endpoint for alerting service"""
    return {"status": "healthy", "service": "alerting"}


@app.get("/alerts", response_model=List[Dict[str, Any]])
async def get_alerts(limit: int = 100, severity: str = None):
    """
    Retrieve recent alerts

    Args:
        limit: Maximum number of alerts to return
        severity: Filter by severity level (optional)
    """
    try:
        alerts = alerting_service.get_alert_history(limit)

        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.severity.value == severity]

        # Convert to dict format for JSON serialization
        alerts_dict = []
        for alert in alerts:
            alerts_dict.append({
                'alert_id': alert.alert_id,
                'rule_id': alert.rule_id,
                'category': alert.category.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'description': alert.description,
                'affected_dataset': alert.affected_dataset,
                'execution_id': alert.execution_id,
                'detection_timestamp': alert.detection_timestamp.isoformat(),
                'status': alert.status.value,
                'evidence': alert.evidence
            })

        return alerts_dict
    except Exception as e:
        logger.error(f"Error retrieving alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")


@app.get("/alerts/{alert_id}", response_model=Dict[str, Any])
async def get_alert(alert_id: str):
    """
    Retrieve a specific alert by ID

    Args:
        alert_id: Alert identifier
    """
    try:
        # This is a simplified implementation - in reality, we'd have a more robust lookup
        alerts = alerting_service.get_alert_history(1000)  # Get all alerts
        for alert in alerts:
            if alert.alert_id == alert_id:
                return {
                    'alert_id': alert.alert_id,
                    'rule_id': alert.rule_id,
                    'category': alert.category.value,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'description': alert.description,
                    'affected_dataset': alert.affected_dataset,
                    'execution_id': alert.execution_id,
                    'detection_timestamp': alert.detection_timestamp.isoformat(),
                    'status': alert.status.value,
                    'evidence': alert.evidence
                }
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving alert: {str(e)}")


@app.get("/incidents", response_model=List[Dict[str, Any]])
async def get_incidents(limit: int = 100, status: str = None):
    """
    Retrieve recent incidents

    Args:
        limit: Maximum number of incidents to return
        status: Filter by incident status (optional)
    """
    try:
        incidents = alerting_service.get_incident_history(limit)

        # Filter by status if specified
        if status:
            incidents = [incident for incident in incidents if incident.status.value == status]

        # Convert to dict format for JSON serialization
        incidents_dict = []
        for incident in incidents:
            incidents_dict.append({
                'incident_id': incident.incident_id,
                'alert_ids': incident.alert_ids,
                'title': incident.title,
                'description': incident.description,
                'severity': incident.severity.value,
                'affected_datasets': incident.affected_datasets,
                'execution_id': incident.execution_id,
                'creation_timestamp': incident.creation_timestamp.isoformat(),
                'last_updated_timestamp': incident.last_updated_timestamp.isoformat(),
                'resolution_timestamp': incident.resolution_timestamp.isoformat() if incident.resolution_timestamp else None,
                'status': incident.status.value
            })

        return incidents_dict
    except Exception as e:
        logger.error(f"Error retrieving incidents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving incidents: {str(e)}")


@app.get("/incidents/{incident_id}", response_model=Dict[str, Any])
async def get_incident(incident_id: str):
    """
    Retrieve a specific incident by ID

    Args:
        incident_id: Incident identifier
    """
    try:
        incident = alerting_service.get_incident(incident_id)
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        return {
            'incident_id': incident.incident_id,
            'alert_ids': incident.alert_ids,
            'title': incident.title,
            'description': incident.description,
            'severity': incident.severity.value,
            'affected_datasets': incident.affected_datasets,
            'execution_id': incident.execution_id,
            'creation_timestamp': incident.creation_timestamp.isoformat(),
            'last_updated_timestamp': incident.last_updated_timestamp.isoformat(),
            'resolution_timestamp': incident.resolution_timestamp.isoformat() if incident.resolution_timestamp else None,
            'status': incident.status.value,
            'resolution_notes': incident.resolution_notes,
            'history': incident.history
        }
    except Exception as e:
        logger.error(f"Error retrieving incident {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving incident: {str(e)}")


@app.post("/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str, notes: str = None):
    """
    Acknowledge an incident

    Args:
        incident_id: Incident identifier
        notes: Notes about acknowledgment
    """
    try:
        success = alerting_service.acknowledge_incident(incident_id, notes)
        if not success:
            raise HTTPException(status_code=404, detail="Incident not found")

        return {"message": f"Incident {incident_id} acknowledged successfully"}
    except Exception as e:
        logger.error(f"Error acknowledging incident {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error acknowledging incident: {str(e)}")


@app.post("/incidents/{incident_id}/resolve")
async def resolve_incident(incident_id: str, resolution_notes: str = None):
    """
    Resolve an incident

    Args:
        incident_id: Incident identifier
        resolution_notes: Notes about resolution
    """
    try:
        success = alerting_service.resolve_incident(incident_id, resolution_notes)
        if not success:
            raise HTTPException(status_code=404, detail="Incident not found")

        return {"message": f"Incident {incident_id} resolved successfully"}
    except Exception as e:
        logger.error(f"Error resolving incident {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resolving incident: {str(e)}")


# Mount this app under /alerts in the main API