"""
Retraining recommendation engine for MLOps framework
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from src.common.runtime_paths import writable_runtime_dir
from src.mlops.models import RetrainingRecommendation, ModelMetadata
from src.mlops.performance import ModelPerformanceTracker
from src.mlops.registry import ModelRegistry

class RetrainingEngine:
    """Recommend model retraining based on various triggers"""

    def __init__(self,
                 registry: ModelRegistry,
                 performance_tracker: ModelPerformanceTracker,
                 retraining_dir: str = "./model_retraining"):
        self.registry = registry
        self.performance_tracker = performance_tracker
        retraining_dir = writable_runtime_dir(retraining_dir)
        self.retraining_dir = Path(retraining_dir)
        self.retraining_dir.mkdir(parents=True, exist_ok=True)

        # Default thresholds (these can be configured externally)
        self.performance_thresholds = {
            'mae_increase_threshold': 0.1,  # 10% increase in MAE
            'rmse_increase_threshold': 0.1,  # 10% increase in RMSE
            'mape_increase_threshold': 0.1,  # 10% increase in MAPE
            'smape_increase_threshold': 0.1,  # 10% increase in SMAPE
            'max_model_age_days': 30,  # Retrain after 30 days
            'drift_score_threshold': 0.1,  # Threshold for drift detection
        }

    def set_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Set custom thresholds for retraining decisions

        Args:
            thresholds: Dictionary of threshold names and values
        """
        self.performance_thresholds.update(thresholds)

    def recommend_retraining(self, model_id: str, model_version: str = None) -> List[RetrainingRecommendation]:
        """
        Generate retraining recommendations for a model

        Args:
            model_id: Model identifier
            model_version: Specific model version (if None, use latest)

        Returns:
            List of retraining recommendations
        """
        recommendations = []

        # Get model metadata
        model = self.registry.get_model(model_id)
        if not model:
            return recommendations

        # If no specific version provided, use current version
        if model_version is None:
            model_version = model.model_version

        # Check model age
        age_recommendation = self._check_model_age(model)
        if age_recommendation:
            recommendations.append(age_recommendation)

        # Check performance degradation
        performance_recommendation = self._check_performance_degradation(model_id, model_version)
        if performance_recommendation:
            recommendations.append(performance_recommendation)

        # Check for drift
        drift_recommendation = self._check_drift(model_id, model_version)
        if drift_recommendation:
            recommendations.append(drift_recommendation)

        # Save recommendations
        for rec in recommendations:
            self.save_recommendation(rec)

        return recommendations

    def _check_model_age(self, model: ModelMetadata) -> Optional[RetrainingRecommendation]:
        """
        Check if model has exceeded maximum age

        Args:
            model: Model metadata

        Returns:
            Retraining recommendation or None
        """
        try:
            # Parse training timestamp
            training_time = datetime.fromisoformat(model.training_timestamp)
            max_age = timedelta(days=self.performance_thresholds['max_model_age_days'])

            if datetime.now() - training_time > max_age:
                return RetrainingRecommendation(
                    model_id=model.model_id,
                    model_version=model.model_version,
                    recommendation_reason=f"Model age ({(datetime.now() - training_time).days} days) exceeds maximum age threshold",
                    recommendation_type="model_age",
                    confidence_score=0.8,
                    suggested_action="retrain",
                    threshold_met=True,
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            print(f"Error checking model age: {e}")

        return None

    def _check_performance_degradation(self, model_id: str, model_version: str) -> Optional[RetrainingRecommendation]:
        """
        Check for performance degradation

        Args:
            model_id: Model identifier
            model_version: Model version

        Returns:
            Retraining recommendation or None
        """
        # Get latest performance
        performance = self.performance_tracker.get_latest_performance(model_id, model_version)
        if not performance:
            return None

        # Compare with historical performance (simplified - in practice we'd compare with baseline)
        # For now, we'll just flag if metrics are unusually high
        metrics = performance.metrics
        degraded = False
        reason = ""

        # Check if any key metrics have increased significantly
        if 'mae' in metrics and metrics['mae'] > 100:  # Arbitrary threshold for demonstration
            degraded = True
            reason = f"High MAE detected: {metrics['mae']}"

        if 'rmse' in metrics and metrics['rmse'] > 150:  # Arbitrary threshold for demonstration
            degraded = True
            reason = f"High RMSE detected: {metrics['rmse']}"

        if degraded:
            return RetrainingRecommendation(
                model_id=model_id,
                model_version=model_version,
                recommendation_reason=reason,
                recommendation_type="performance_degradation",
                confidence_score=0.7,
                suggested_action="retrain",
                threshold_met=True,
                timestamp=datetime.now().isoformat()
            )

        return None

    def _check_drift(self, model_id: str, model_version: str) -> Optional[RetrainingRecommendation]:
        """
        Check for data or prediction drift

        Args:
            model_id: Model identifier
            model_version: Model version

        Returns:
            Retraining recommendation or None
        """
        # This would involve checking drift detection results
        # For now, we'll return None to indicate no drift detected
        # In a real implementation, this would check recent drift results

        # For demonstration purposes, let's assume no drift
        return None

    def save_recommendation(self, recommendation: RetrainingRecommendation) -> None:
        """
        Save retraining recommendation to persistent storage

        Args:
            recommendation: Retraining recommendation to save
        """
        recommendation_file = self.retraining_dir / f"{recommendation.model_id}_{recommendation.model_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        recommendation_dict = {
            'model_id': recommendation.model_id,
            'model_version': recommendation.model_version,
            'recommendation_reason': recommendation.recommendation_reason,
            'recommendation_type': recommendation.recommendation_type,
            'confidence_score': recommendation.confidence_score,
            'suggested_action': recommendation.suggested_action,
            'threshold_met': recommendation.threshold_met,
            'timestamp': recommendation.timestamp
        }

        with open(recommendation_file, 'w') as f:
            json.dump(recommendation_dict, f, indent=2)

    def get_recommendations_history(self, model_id: str, limit: int = 10) -> List[RetrainingRecommendation]:
        """
        Get retraining recommendations history for a model

        Args:
            model_id: Model identifier
            limit: Maximum number of recommendations to return

        Returns:
            List of retraining recommendations
        """
        recommendations = []
        for rec_file in self.retraining_dir.glob(f"{model_id}_*.json"):
            try:
                with open(rec_file, 'r') as f:
                    rec_dict = json.load(f)
                    recommendation = RetrainingRecommendation(
                        model_id=rec_dict['model_id'],
                        model_version=rec_dict['model_version'],
                        recommendation_reason=rec_dict['recommendation_reason'],
                        recommendation_type=rec_dict['recommendation_type'],
                        confidence_score=rec_dict['confidence_score'],
                        suggested_action=rec_dict['suggested_action'],
                        threshold_met=rec_dict['threshold_met'],
                        timestamp=rec_dict['timestamp']
                    )
                    recommendations.append(recommendation)
            except Exception as e:
                print(f"Error loading recommendation {rec_file}: {e}")
                continue

        # Sort by timestamp descending and limit results
        recommendations.sort(key=lambda x: x.timestamp, reverse=True)
        return recommendations[:limit]

    def simulate_retraining_workflow(self, model_id: str, model_version: str) -> Dict[str, Any]:
        """
        Simulate a retraining workflow for testing purposes

        Args:
            model_id: Model identifier
            model_version: Model version

        Returns:
            Dictionary with simulation results
        """
        # This is a simulation - in a real system this would trigger actual retraining
        return {
            'model_id': model_id,
            'model_version': model_version,
            'simulation_status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'notes': 'Simulated retraining workflow for testing purposes'
        }