"""
Model rollback functionality for MLOps framework
"""

import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from src.common.runtime_paths import writable_runtime_dir
from src.mlops.models import ModelMetadata, ModelLifecycleState, RollbackRecord
from src.mlops.registry import ModelRegistry

class ModelRollbackEngine:
    """Handle model rollback operations"""

    def __init__(self,
                 registry: ModelRegistry,
                 rollback_dir: str = "./model_rollback"):
        self.registry = registry
        rollback_dir = writable_runtime_dir(rollback_dir)
        self.rollback_dir = Path(rollback_dir)
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

    def rollback_model(self, model_id: str, target_version: str,
                      rollback_reason: str, rollback_user: str = None) -> Dict[str, Any]:
        """
        Rollback a model to a previous version

        Args:
            model_id: Model identifier
            target_version: Version to rollback to
            rollback_reason: Reason for rollback
            rollback_user: User initiating rollback (optional)

        Returns:
            Rollback results
        """
        # Get current model
        current_model = self.registry.get_model(model_id)
        if not current_model:
            return {'error': 'Model not found'}

        # Get target model version
        target_model = self.registry.get_model(model_id)
        if not target_model:
            return {'error': 'Target version not found'}

        # Store current production version
        current_production_version = None
        if current_model.model_status == ModelLifecycleState.PRODUCTION:
            current_production_version = current_model.model_version

        # Update model status to PRODUCTION (rolling back to target version)
        success = self.registry.update_model_status(model_id, ModelLifecycleState.PRODUCTION)
        if not success:
            return {'error': 'Failed to update model status'}

        # Create rollback record
        rollback_record = RollbackRecord(
            model_id=model_id,
            rolled_back_from_version=current_production_version or "unknown",
            rolled_back_to_version=target_version,
            rollback_reason=rollback_reason,
            rollback_timestamp=datetime.now().isoformat(),
            rollback_user=rollback_user
        )

        # Save rollback record
        self.registry.save_rollback_record(rollback_record)

        return {
            'status': 'rolled_back',
            'model_id': model_id,
            'rolled_back_from': current_production_version or "unknown",
            'rolled_back_to': target_version,
            'rollback_reason': rollback_reason,
            'rollback_timestamp': datetime.now().isoformat(),
            'rollback_user': rollback_user
        }

    def get_rollback_history(self, model_id: str) -> List[RollbackRecord]:
        """
        Get rollback history for a model

        Args:
            model_id: Model identifier

        Returns:
            List of rollback records
        """
        return self.registry.get_rollback_history(model_id)

    def get_model_versions_history(self, model_id: str) -> Dict[str, Any]:
        """
        Get complete version history for a model including promotions and rollbacks

        Args:
            model_id: Model identifier

        Returns:
            History of model versions and events
        """
        # Get all versions of the model
        versions = self.registry.get_model_versions(model_id)

        # Get promotion history
        promotion_history = self.registry.get_promotion_history(model_id)

        # Get rollback history
        rollback_history = self.get_rollback_history(model_id)

        # Combine and sort by timestamp
        events = []

        # Add promotions
        for promotion in promotion_history:
            events.append({
                'type': 'promotion',
                'version': promotion.model_version,
                'timestamp': promotion.decision_timestamp,
                'details': promotion.promotion_reason
            })

        # Add rollbacks
        for rollback in rollback_history:
            events.append({
                'type': 'rollback',
                'from_version': rollback.rolled_back_from_version,
                'to_version': rollback.rolled_back_to_version,
                'timestamp': rollback.rollback_timestamp,
                'details': rollback.rollback_reason
            })

        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'])

        return {
            'model_id': model_id,
            'versions': versions,
            'events': events
        }

    def validate_rollback_safety(self, model_id: str, target_version: str) -> Dict[str, Any]:
        """
        Validate if a rollback is safe (checks for existence of target version)

        Args:
            model_id: Model identifier
            target_version: Version to rollback to

        Returns:
            Validation results
        """
        # Check if target version exists
        versions = self.registry.get_model_versions(model_id)
        if target_version not in versions:
            return {
                'valid': False,
                'error': f'Target version {target_version} does not exist for model {model_id}'
            }

        # Check if model exists
        model = self.registry.get_model(model_id)
        if not model:
            return {
                'valid': False,
                'error': f'Model {model_id} not found'
            }

        # Check if target version is not the only version
        if len(versions) <= 1:
            return {
                'valid': False,
                'error': 'Cannot rollback - this is the only version of the model'
            }

        return {
            'valid': True,
            'message': f'Rollback to version {target_version} is safe'
        }

    def restore_model_state(self, model_id: str, timestamp: str) -> Dict[str, Any]:
        """
        Restore model to a specific state based on timestamp

        Args:
            model_id: Model identifier
            timestamp: Timestamp to restore to

        Returns:
            Restore results
        """
        # This would require more complex history tracking
        # For now, we'll just return a placeholder
        return {
            'status': 'not_implemented',
            'message': 'Model state restoration not yet implemented'
        }