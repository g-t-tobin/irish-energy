"""
Integration with existing observability and alerting systems
"""

import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from src.mlops.models import ModelMetadata, ModelLifecycleState
from src.mlops.registry import ModelRegistry
from src.mlops.performance import ModelPerformanceTracker
from src.mlops.drift import DriftDetector
from src.mlops.retraining import RetrainingEngine
from src.mlops.promotion import ModelPromotionEngine
from src.mlops.rollback import ModelRollbackEngine

# Import existing alerting system
from src.alerting.alert_manager import AlertManager
from src.observability.logger import Logger

class MLOpsIntegration:
    """Integrate MLOps components with existing observability and alerting"""

    def __init__(self,
                 registry: ModelRegistry,
                 performance_tracker: ModelPerformanceTracker,
                 drift_detector: DriftDetector,
                 retraining_engine: RetrainingEngine,
                 promotion_engine: ModelPromotionEngine,
                 rollback_engine: ModelRollbackEngine,
                 alert_manager: AlertManager = None,
                 logger: Logger = None):
        self.registry = registry
        self.performance_tracker = performance_tracker
        self.drift_detector = drift_detector
        self.retraining_engine = retraining_engine
        self.promotion_engine = promotion_engine
        self.rollback_engine = rollback_engine
        self.alert_manager = alert_manager
        self.logger = logger or Logger()

    def create_alert_for_performance_degradation(self, model_id: str, model_version: str,
                                               degradation_details: Dict[str, Any]) -> Optional[str]:
        """
        Create alert for model performance degradation

        Args:
            model_id: Model identifier
            model_version: Model version
            degradation_details: Details about the degradation

        Returns:
            Alert ID or None if no alert created
        """
        if not self.alert_manager:
            return None

        # Create alert message
        alert_message = f"Model {model_id} version {model_version} shows performance degradation"
        alert_details = {
            'model_id': model_id,
            'model_version': model_version,
            'degradation_type': degradation_details.get('type', 'unknown'),
            'metrics': degradation_details.get('metrics', {}),
            'timestamp': datetime.now().isoformat()
        }

        # Create alert
        alert_id = self.alert_manager.create_alert(
            alert_type="model_performance_degradation",
            severity="warning",
            message=alert_message,
            details=alert_details
        )

        return alert_id

    def create_alert_for_drift_detection(self, drift_result: Dict[str, Any]) -> Optional[str]:
        """
        Create alert for drift detection

        Args:
            drift_result: Drift detection result

        Returns:
            Alert ID or None if no alert created
        """
        if not self.alert_manager:
            return None

        # Create alert message
        alert_message = f"Drift detected in feature '{drift_result.get('feature_name', 'unknown')}'"
        alert_details = {
            'feature_name': drift_result.get('feature_name', 'unknown'),
            'drift_score': drift_result.get('drift_score', 0.0),
            'drift_detected': drift_result.get('drift_detected', False),
            'timestamp': datetime.now().isoformat()
        }

        # Create alert
        alert_id = self.alert_manager.create_alert(
            alert_type="model_drift_detection",
            severity="warning",
            message=alert_message,
            details=alert_details
        )

        return alert_id

    def create_alert_for_retraining_recommendation(self, recommendation: Dict[str, Any]) -> Optional[str]:
        """
        Create alert for retraining recommendation

        Args:
            recommendation: Retraining recommendation

        Returns:
            Alert ID or None if no alert created
        """
        if not self.alert_manager:
            return None

        # Create alert message
        alert_message = f"Retraining recommended for model {recommendation.get('model_id', 'unknown')}"
        alert_details = {
            'model_id': recommendation.get('model_id', 'unknown'),
            'model_version': recommendation.get('model_version', 'unknown'),
            'recommendation_reason': recommendation.get('recommendation_reason', ''),
            'confidence_score': recommendation.get('confidence_score', 0.0),
            'timestamp': datetime.now().isoformat()
        }

        # Create alert
        alert_id = self.alert_manager.create_alert(
            alert_type="model_retraining_recommendation",
            severity="info",
            message=alert_message,
            details=alert_details
        )

        return alert_id

    def create_alert_for_promotion_decision(self, promotion_decision: Dict[str, Any]) -> Optional[str]:
        """
        Create alert for model promotion decision

        Args:
            promotion_decision: Promotion decision details

        Returns:
            Alert ID or None if no alert created
        """
        if not self.alert_manager:
            return None

        # Create alert message
        status = "approved" if promotion_decision.get('approved', False) else "rejected"
        alert_message = f"Model promotion {status}: {promotion_decision.get('model_id', 'unknown')}"
        alert_details = {
            'model_id': promotion_decision.get('model_id', 'unknown'),
            'model_version': promotion_decision.get('model_version', 'unknown'),
            'status': status,
            'reason': promotion_decision.get('promotion_reason', ''),
            'timestamp': datetime.now().isoformat()
        }

        # Create alert
        alert_id = self.alert_manager.create_alert(
            alert_type="model_promotion_decision",
            severity="info",
            message=alert_message,
            details=alert_details
        )

        return alert_id

    def create_alert_for_rollback_event(self, rollback_record: Dict[str, Any]) -> Optional[str]:
        """
        Create alert for model rollback event

        Args:
            rollback_record: Rollback event details

        Returns:
            Alert ID or None if no alert created
        """
        if not self.alert_manager:
            return None

        # Create alert message
        alert_message = f"Model rollback occurred: {rollback_record.get('model_id', 'unknown')}"
        alert_details = {
            'model_id': rollback_record.get('model_id', 'unknown'),
            'rolled_back_from': rollback_record.get('rolled_back_from_version', 'unknown'),
            'rolled_back_to': rollback_record.get('rolled_back_to_version', 'unknown'),
            'reason': rollback_record.get('rollback_reason', ''),
            'timestamp': datetime.now().isoformat()
        }

        # Create alert
        alert_id = self.alert_manager.create_alert(
            alert_type="model_rollback_event",
            severity="info",
            message=alert_message,
            details=alert_details
        )

        return alert_id

    def monitor_model_health(self, model_id: str) -> Dict[str, Any]:
        """
        Monitor overall health of a model including performance, drift, and status

        Args:
            model_id: Model identifier

        Returns:
            Health status report
        """
        model = self.registry.get_model(model_id)
        if not model:
            return {'error': 'Model not found'}

        # Get performance data
        performance = self.performance_tracker.get_latest_performance(model_id, model.model_version)

        # Get model status
        status = model.model_status.value

        # Log health check
        self.logger.info(f"Monitoring health for model {model_id}: status={status}")

        health_report = {
            'model_id': model_id,
            'model_version': model.model_version,
            'status': status,
            'performance': performance.metrics if performance else {},
            'timestamp': datetime.now().isoformat(),
            'alerts': []
        }

        # Check for potential issues
        if performance and 'mae' in performance.metrics:
            # Example: flag high MAE
            if performance.metrics['mae'] > 100:  # Threshold for demonstration
                alert_id = self.create_alert_for_performance_degradation(
                    model_id, model.model_version,
                    {
                        'type': 'high_mae',
                        'metrics': {'mae': performance.metrics['mae']}
                    }
                )
                if alert_id:
                    health_report['alerts'].append(alert_id)

        return health_report

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive MLOps report

        Returns:
            Comprehensive report with all system status
        """
        # Get all models
        models = self.registry.list_models()

        # Group models by category
        models_by_category = {}
        for model in models:
            category = model.forecasting_category
            if category not in models_by_category:
                models_by_category[category] = []
            models_by_category[category].append(model)

        # Get performance summary
        performance_summary = {}
        for category, category_models in models_by_category.items():
            # Find production model for this category
            production_model = self.registry.get_production_model(category)
            if production_model:
                performance = self.performance_tracker.get_latest_performance(
                    production_model.model_id, production_model.model_version
                )
                if performance:
                    performance_summary[category] = {
                        'model_id': production_model.model_id,
                        'model_version': production_model.model_version,
                        'metrics': performance.metrics,
                        'evaluation_timestamp': performance.evaluation_timestamp
                    }

        # Get recent alerts
        recent_alerts = []  # Would pull from alert manager if available

        # Get promotion history
        promotion_history = []
        for model in models:
            if model.model_status == ModelLifecycleState.PRODUCTION:
                history = self.registry.get_promotion_history(model.model_id)
                for decision in history[-3:]:  # Last 3 promotions
                    promotion_history.append({
                        'model_id': decision.model_id,
                        'model_version': decision.model_version,
                        'timestamp': decision.decision_timestamp,
                        'approved': decision.approved
                    })

        report = {
            'generated_at': datetime.now().isoformat(),
            'total_models': len(models),
            'models_by_category': models_by_category,
            'performance_summary': performance_summary,
            'recent_alerts': recent_alerts,
            'promotion_history': promotion_history,
            'system_health': 'healthy'  # Simplified health status
        }

        return report