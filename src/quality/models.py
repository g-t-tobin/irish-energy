"""
Data quality models for Irish Energy Analytics Data Platform
"""
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


class QualityStatus(Enum):
    """Enumeration of quality assessment statuses"""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


@dataclass
class QualityRuleResult:
    """Represents the result of a single quality rule evaluation"""
    rule_name: str
    status: QualityStatus
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class QualityReport:
    """Represents a complete quality assessment report"""
    dataset_name: str
    data_layer: str
    pipeline_date: str
    assessment_timestamp: datetime
    total_records: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    overall_score: float
    quality_status: QualityStatus
    rule_results: List[QualityRuleResult]
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert quality report to dictionary format"""
        return {
            'dataset_name': self.dataset_name,
            'data_layer': self.data_layer,
            'pipeline_date': self.pipeline_date,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'total_records': self.total_records,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'warning_checks': self.warning_checks,
            'overall_score': self.overall_score,
            'quality_status': self.quality_status.value,
            'rule_results': [
                {
                    'rule_name': result.rule_name,
                    'status': result.status.value,
                    'message': result.message,
                    'details': result.details
                } for result in self.rule_results
            ],
            'explanation': self.explanation
        }


class QualityRule(TypedDict):
    """Typed dictionary for quality rule specification"""
    name: str
    severity: str  # 'critical', 'warning', 'info'
    description: str
    check_function: callable
    weight: float