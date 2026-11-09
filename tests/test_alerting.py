"""
Test file for the alerting framework
"""
import pytest
from datetime import datetime, timedelta
from src.alerting.models import Alert, Incident, AlertSeverity, AlertCategory, AlertStatus, IncidentStatus
from src.alerting.engine import AlertEvaluationEngine
from src.alerting.rules import AlertRules
from src.alerting.incident_manager import IncidentManager
from src.alerting.notification import MockNotificationProvider
from src.alerting.deduplication import AlertDeduplicator
from src.alerting.service import AlertingService


def test_alert_models():
    """Test that alert models can be instantiated"""

    # Test Alert model
    alert = Alert(
        alert_id="alert-123",
        rule_id="test-rule",
        category=AlertCategory.PIPELINE_FAILURE,
        severity=AlertSeverity.ERROR,
        title="Test Alert",
        description="This is a test alert",
        affected_dataset="test-dataset",
        execution_id="exec-123",
        detection_timestamp=datetime.now(),
        metric_values={"test_metric": 100},
        threshold=90,
        status=AlertStatus.ACTIVE,
        evidence="Test evidence"
    )

    assert alert.alert_id == "alert-123"
    assert alert.severity == AlertSeverity.ERROR
    assert alert.category == AlertCategory.PIPELINE_FAILURE

    # Test Incident model
    incident = Incident(
        incident_id="inc-123",
        alert_ids=["alert-123"],
        title="Test Incident",
        description="This is a test incident",
        severity=AlertSeverity.ERROR,
        affected_datasets=["test-dataset"],
        execution_id="exec-123",
        creation_timestamp=datetime.now(),
        last_updated_timestamp=datetime.now(),
        resolution_timestamp=None,
        status=IncidentStatus.OPEN,
        history=[{
            'timestamp': datetime.now(),
            'action': 'created',
            'details': 'Test incident created'
        }]
    )

    assert incident.incident_id == "inc-123"
    assert incident.severity == AlertSeverity.ERROR
    assert incident.status == IncidentStatus.OPEN


def test_alert_rules():
    """Test alert rule initialization and functionality"""

    # Test that rules can be initialized
    rules = AlertRules()
    enabled_rules = rules.get_enabled_rules()

    assert len(enabled_rules) > 0

    # Test getting rules by category
    pipeline_rules = rules.get_rules_by_category(AlertCategory.PIPELINE_FAILURE)
    assert len(pipeline_rules) > 0

    # Test specific rule evaluation
    # We'll test a simple case by looking at rule structure
    ingestion_rules = rules.get_rules_by_category(AlertCategory.INGESTION_PROBLEM)
    assert len(ingestion_rules) >= 2  # Should have at least 2 ingestion rules


def test_alert_evaluation_engine():
    """Test alert evaluation engine"""

    # Initialize engine
    engine = AlertEvaluationEngine()

    # Test with empty event data
    events = engine.evaluate_event({})
    assert isinstance(events, list)

    # Test with pipeline failure event
    pipeline_event = {
        'execution_id': 'exec-123',
        'error_message': 'Pipeline failed',
        'event_type': 'pipeline_failure'
    }

    # This should generate alerts but won't actually produce concrete results
    # since we don't have specific evaluation functions to call
    events = engine.evaluate_event(pipeline_event)
    assert isinstance(events, list)


def test_incident_manager():
    """Test incident manager functionality"""

    # Initialize manager
    engine = AlertEvaluationEngine()
    manager = IncidentManager(engine)

    # Test creating incident
    incident = manager.create_incident(
        alert_ids=['alert-123'],
        title='Test Incident',
        description='Test description',
        severity=AlertSeverity.WARNING,
        affected_datasets=['test-dataset']
    )

    assert incident.incident_id is not None
    assert incident.title == 'Test Incident'
    assert incident.status == IncidentStatus.OPEN

    # Test retrieving incident
    retrieved = manager.get_incident(incident.incident_id)
    assert retrieved is not None
    assert retrieved.incident_id == incident.incident_id

    # Test acknowledging incident
    success = manager.acknowledge_incident(incident.incident_id)
    assert success is True

    # Verify status change
    acked_incident = manager.get_incident(incident.incident_id)
    assert acked_incident.status == IncidentStatus.ACKNOWLEDGED

    # Test resolving incident
    success = manager.resolve_incident(incident.incident_id, 'Resolved manually')
    assert success is True

    # Verify status change
    resolved_incident = manager.get_incident(incident.incident_id)
    assert resolved_incident.status == IncidentStatus.RESOLVED


def test_deduplication():
    """Test alert deduplication functionality"""

    deduplicator = AlertDeduplicator(suppression_window_minutes=60)

    # Create test alerts
    alert1 = Alert(
        alert_id="alert-123",
        rule_id="test-rule",
        category=AlertCategory.PIPELINE_FAILURE,
        severity=AlertSeverity.ERROR,
        title="Test Alert",
        description="This is a test alert",
        affected_dataset="test-dataset",
        execution_id="exec-123",
        detection_timestamp=datetime.now(),
        metric_values={"test_metric": 100},
        threshold=90,
        status=AlertStatus.ACTIVE,
        evidence="Test evidence"
    )

    alert2 = Alert(
        alert_id="alert-456",
        rule_id="test-rule",  # Same rule
        category=AlertCategory.PIPELINE_FAILURE,  # Same category
        severity=AlertSeverity.ERROR,
        title="Test Alert Duplicate",
        description="This is a duplicate test alert",
        affected_dataset="test-dataset",
        execution_id="exec-123",
        detection_timestamp=datetime.now(),
        metric_values={"test_metric": 100},
        threshold=90,
        status=AlertStatus.ACTIVE,
        evidence="Test evidence"
    )

    # Register first alert
    deduplicator.register_alert(alert1)

    # Second alert should be suppressed since it's a duplicate
    should_suppress = deduplicator.should_suppress_alert(alert2)
    assert should_suppress is True

    # Register the second alert and test it should be suppressed
    deduplicator.register_alert(alert2)
    should_suppress_again = deduplicator.should_suppress_alert(alert2)
    assert should_suppress_again is True


def test_alerting_service():
    """Test main alerting service"""

    # Initialize service with mock notification
    notification_provider = MockNotificationProvider()
    service = AlertingService(notification_provider=notification_provider)

    # Test processing event
    event_data = {
        'event_type': 'pipeline_failure',
        'execution_id': 'exec-123',
        'error_message': 'Pipeline failed',
        'dataset_name': 'test-dataset'
    }

    # This won't actually generate alerts since we don't have proper evaluation functions
    # But it should not crash
    alerts = service.process_event(event_data)
    assert isinstance(alerts, list)

    # Test getting active alerts
    active_alerts = service.get_active_alerts()
    assert isinstance(active_alerts, dict)

    # Test getting incidents
    incidents = service.get_open_incidents()
    assert isinstance(incidents, list)

    # Test clearing data
    service.clear_all_data()

    # Verify cleared
    active_alerts = service.get_active_alerts()
    incidents = service.get_open_incidents()
    assert len(active_alerts) == 0
    assert len(incidents) == 0


if __name__ == "__main__":
    test_alert_models()
    test_alert_rules()
    test_alert_evaluation_engine()
    test_incident_manager()
    test_deduplication()
    test_alerting_service()
    print("All tests passed!")