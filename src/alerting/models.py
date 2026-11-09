"""
Alerting models for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class AlertSeverity(Enum):
    """Enumeration of alert severities"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertStatus(Enum):
    """Enumeration of alert statuses"""
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"


class IncidentStatus(Enum):
    """Enumeration of incident statuses"""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlertCategory(Enum):
    """Enumeration of alert categories"""
    PIPELINE_FAILURE = "PIPELINE_FAILURE"
    INGESTION_PROBLEM = "INGESTION_PROBLEM"
    DATA_FRESHNESS = "DATA_FRESHNESS"
    DATA_QUALITY = "DATA_QUALITY"
    PERFORMANCE = "PERFORMANCE"


@dataclass
class Alert:
    """Represents an alert instance"""
    alert_id: str
    rule_id: str
    category: AlertCategory
    severity: AlertSeverity
    title: str
    description: str
    affected_dataset: Optional[str]
    execution_id: Optional[str]
    detection_timestamp: datetime
    metric_values: Optional[Dict[str, Any]]
    threshold: Optional[Union[float, int]]
    status: AlertStatus
    evidence: Optional[str] = None


@dataclass
class Incident:
    """Represents an incident record"""
    incident_id: str
    alert_ids: List[str]
    title: str
    description: str
    severity: AlertSeverity
    affected_datasets: List[str]
    execution_id: Optional[str]
    creation_timestamp: datetime
    last_updated_timestamp: datetime
    resolution_timestamp: Optional[datetime]
    status: IncidentStatus
    resolution_notes: Optional[str] = None
    history: List[Dict[str, Any]] = None


class AlertRule(TypedDict):
    """Typed dictionary for alert rule specification"""
    rule_id: str
    category: AlertCategory
    severity: AlertSeverity
    title: str
    description: str
    enabled: bool
    threshold: Optional[Union[float, int]]
    window_minutes: Optional[int]
    evaluation_function: callable


class AlertEvent(TypedDict):
    """Typed dictionary for alert event specification"""
    alert_id: str
    rule_id: str
    category: AlertCategory
    severity: AlertSeverity
    affected_dataset: Optional[str]
    execution_id: Optional[str]
    timestamp: datetime
    metric_values: Optional[Dict[str, Any]]
    evidence: str