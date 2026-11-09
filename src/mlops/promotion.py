"""
Model evaluation and promotion controls for MLOps framework
"""

import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from src.common.runtime_paths import writable_runtime_dir
from src.mlops.models import ModelMetadata, ModelLifecycleState, PromotionDecision
from src.mlops.registry import ModelRegistry
from src.mlops.performance import ModelPerformanceTracker
from src.mlops.drift import DriftDetector

class ModelPromotionEngine:
    """Handle model evaluation, promotion, and lifecycle management"""

    def __init__(self,
                 registry: ModelRegistry,
                 performance_tracker: ModelPerformanceTracker,
                 drift_detector: DriftDetector,
                 promotion_dir: str = "./model_promotion"):
        self.registry = registry
        self.performance_tracker = performance_tracker
        self.drift_detector = drift_detector
        promotion_dir = writable_runtime_dir(promotion_dir)
        self.promotion_dir = Path(promotion_dir)
        self.promotion_dir.mkdir(parents=True, exist_ok=True)

        # Default promotion criteria
        self.promotion_criteria = {
            'min_performance_thresholds': {
                'mae': 0.0,      # Minimum acceptable MAE
                'rmse': 0.0,     # Minimum acceptable RMSE
                'mape': 100.0,   # Maximum acceptable MAPE (percentage)
                'smape': 100.0,  # Maximum acceptable SMAPE (percentage)
            },
            'requirement_comparison': True,  # Require comparison with current production model
            'minimum_evaluation_period': 30,  # Minimum days of evaluation data
        }

    def set_promotion_criteria(self, criteria: Dict[str, Any]) -> None:
        """
        Set custom promotion criteria

        Args:
            criteria: Dictionary of promotion criteria
        """
        self.promotion_criteria.update(criteria)

    def evaluate_candidate_model(self, model_id: str, model_version: str) -> Dict[str, Any]:
        """
        Evaluate a candidate model for promotion

        Args:
            model_id: Model identifier
            model_version: Model version

        Returns:
            Evaluation results
        """
        model = self.registry.get_model(model_id)
        if not model:
            return {'error': 'Model not found'}

        # Get performance metrics
        performance = self.performance_tracker.get_latest_performance(model_id, model_version)
        if not performance:
            return {'error': 'No performance data available'}

        # Get current production model for comparison
        current_production = self.registry.get_production_model(model.forecasting_category)

        # Perform evaluation
        evaluation_results = {
            'model_id': model_id,
            'model_version': model_version,
            'evaluation_timestamp': datetime.now().isoformat(),
            'metrics': performance.metrics,
            'evaluation_period': performance.evaluation_period,
            'observation_count': performance.observation_count,
            'comparison_with_production': None,
            'evaluation_passed': True,
            'evaluation_comments': [],
        }

        # Compare with current production model if available
        if current_production:
            current_performance = self.performance_tracker.get_latest_performance(
                current_production.model_id, current_production.model_version
            )

            if current_performance:
                # Compare metrics
                comparison = {}
                for metric_name, metric_value in performance.metrics.items():
                    if metric_name in current_performance.metrics:
                        current_value = current_performance.metrics[metric_name]
                        improvement = (current_value - metric_value) / current_value if current_value != 0 else 0
                        comparison[metric_name] = {
                            'current': current_value,
                            'candidate': metric_value,
                            'improvement': improvement
                        }

                evaluation_results['comparison_with_production'] = comparison

                # Check if candidate is better
                better_than_current = True
                for metric_name, values in comparison.items():
                    if metric_name in ['mae', 'rmse']:  # Lower is better
                        if values['candidate'] > values['current']:
                            better_than_current = False
                            evaluation_results['evaluation_comments'].append(
                                f"Worse {metric_name} performance compared to production model"
                            )
                    elif metric_name in ['mape', 'smape']:  # Lower is better (but percentage)
                        if values['candidate'] > values['current']:
                            better_than_current = False
                            evaluation_results['evaluation_comments'].append(
                                f"Worse {metric_name} performance compared to production model"
                            )

                if not better_than_current:
                    evaluation_results['evaluation_passed'] = False
                    evaluation_results['evaluation_comments'].append(
                        "Candidate model does not outperform current production model"
                    )

        # Apply performance thresholds
        for metric_name, threshold in self.promotion_criteria['min_performance_thresholds'].items():
            if metric_name in performance.metrics:
                if metric_name in ['mape', 'smape']:
                    # These are percentages, so higher is worse
                    if performance.metrics[metric_name] > threshold:
                        evaluation_results['evaluation_passed'] = False
                        evaluation_results['evaluation_comments'].append(
                            f"{metric_name.upper()} exceeds threshold of {threshold}%"
                        )
                else:
                    # These are absolute values, so lower is better
                    if performance.metrics[metric_name] < threshold:
                        evaluation_results['evaluation_passed'] = False
                        evaluation_results['evaluation_comments'].append(
                            f"{metric_name.upper()} below threshold of {threshold}"
                        )

        return evaluation_results

    def promote_model(self, model_id: str, model_version: str = None) -> Dict[str, Any]:
        """
        Promote a candidate model to production

        Args:
            model_id: Model identifier
            model_version: Model version to promote (if None, promote latest candidate)

        Returns:
            Promotion results
        """
        # Get model metadata
        model = self.registry.get_model(model_id)
        if not model:
            return {'error': 'Model not found'}

        # If no version specified, get latest candidate version
        if model_version is None:
            model_version = model.model_version

        # Ensure model is in CANDIDATE state
        if model.model_status != ModelLifecycleState.CANDIDATE:
            return {
                'error': 'Model is not in CANDIDATE state',
                'current_status': model.model_status.value
            }

        # Evaluate the candidate model
        evaluation = self.evaluate_candidate_model(model_id, model_version)
        if 'error' in evaluation:
            return evaluation

        # Check if evaluation passed
        if not evaluation['evaluation_passed']:
            # Record rejection
            self._record_model_rejection(model_id, model_version, evaluation)
            return {
                'status': 'rejected',
                'reason': 'Evaluation did not meet promotion criteria',
                'details': evaluation
            }

        # Get current production model
        current_production = self.registry.get_production_model(model.forecasting_category)

        # Promote model
        success = self.registry.update_model_status(model_id, ModelLifecycleState.PRODUCTION)
        if not success:
            return {'error': 'Failed to update model status'}

        # Record promotion decision
        promotion_decision = PromotionDecision(
            model_id=model_id,
            model_version=model_version,
            previous_production_version=current_production.model_version if current_production else None,
            promotion_reason="Passed evaluation criteria",
            evaluation_results=evaluation,
            decision_timestamp=datetime.now().isoformat(),
            approved=True
        )

        self.registry.save_promotion_decision(promotion_decision)

        return {
            'status': 'promoted',
            'model_id': model_id,
            'model_version': model_version,
            'previous_production_version': current_production.model_version if current_production else None,
            'promotion_timestamp': datetime.now().isoformat()
        }

    def _record_model_rejection(self, model_id: str, model_version: str, evaluation: Dict[str, Any]) -> None:
        """Record model rejection for future reference"""
        # Update model status to REJECTED
        self.registry.update_model_status(model_id, ModelLifecycleState.REJECTED)

        # Record rejection details (would typically be saved to a rejection log)
        pass

    def reject_candidate_model(self, model_id: str, model_version: str, reason: str) -> Dict[str, Any]:
        """
        Reject a candidate model

        Args:
            model_id: Model identifier
            model_version: Model version
            reason: Reason for rejection

        Returns:
            Rejection results
        """
        # Update model status to REJECTED
        success = self.registry.update_model_status(model_id, ModelLifecycleState.REJECTED)
        if not success:
            return {'error': 'Failed to update model status'}

        return {
            'status': 'rejected',
            'model_id': model_id,
            'model_version': model_version,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }

    def archive_model(self, model_id: str, model_version: str = None) -> Dict[str, Any]:
        """
        Archive a model (move to archive state)

        Args:
            model_id: Model identifier
            model_version: Model version (if None, use latest)

        Returns:
            Archive results
        """
        model = self.registry.get_model(model_id)
        if not model:
            return {'error': 'Model not found'}

        # Update model status to ARCHIVED
        success = self.registry.update_model_status(model_id, ModelLifecycleState.ARCHIVED)
        if not success:
            return {'error': 'Failed to update model status'}

        return {
            'status': 'archived',
            'model_id': model_id,
            'model_version': model_version or model.model_version,
            'timestamp': datetime.now().isoformat()
        }

    def get_promotion_history(self, model_id: str) -> List[PromotionDecision]:
        """
        Get promotion history for a model

        Args:
            model_id: Model identifier

        Returns:
            List of promotion decisions
        """
        return self.registry.get_promotion_history(model_id)

    def get_model_lifecycle_status(self, model_id: str) -> Dict[str, Any]:
        """
        Get the complete lifecycle status of a model

        Args:
            model_id: Model identifier

        Returns:
            Lifecycle status information
        """
        model = self.registry.get_model(model_id)
        if not model:
            return {'error': 'Model not found'}

        # Get promotion history
        promotion_history = self.get_promotion_history(model_id)

        # Get rollback history
        rollback_history = self.registry.get_rollback_history(model_id)

        return {
            'model_id': model.model_id,
            'model_name': model.model_name,
            'model_version': model.model_version,
            'model_status': model.model_status.value,
            'forecasting_category': model.forecasting_category,
            'training_timestamp': model.training_timestamp,
            'promotion_history': [
                {
                    'version': decision.model_version,
                    'timestamp': decision.decision_timestamp,
                    'approved': decision.approved,
                    'reason': decision.promotion_reason
                } for decision in promotion_history
            ],
            'rollback_history': [
                {
                    'from_version': record.rolled_back_from_version,
                    'to_version': record.rolled_back_to_version,
                    'timestamp': record.rollback_timestamp,
                    'reason': record.rollback_reason
                } for record in rollback_history
            ]
        }