"""
Model registry for tracking forecasting models throughout their lifecycle
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from src.common.runtime_paths import writable_runtime_dir
from src.mlops.models import ModelMetadata, ModelLifecycleState, PromotionDecision, RollbackRecord
from src.forecasting.models import ForecastModel
from src.forecasting.renewable_models import RenewableForecastModel

class ModelRegistry:
    """Lightweight model registry for forecasting models"""

    def __init__(self, registry_dir: str = "./model_registry"):
        registry_dir = writable_runtime_dir(registry_dir)
        self.registry_dir = Path(registry_dir)
        self.metadata_dir = self.registry_dir / "metadata"
        self.artifacts_dir = self.registry_dir / "artifacts"
        self.promotion_history_dir = self.registry_dir / "promotion_history"
        self.rollback_history_dir = self.registry_dir / "rollback_history"

        # Create directories if they don't exist
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.promotion_history_dir.mkdir(parents=True, exist_ok=True)
        self.rollback_history_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for quick access
        self._cache = {}
        self._load_cache()

    def _load_cache(self):
        """Load metadata cache from disk"""
        self._cache = {}
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    model_id = metadata.get('model_id')
                    if model_id:
                        self._cache[model_id] = metadata
            except Exception as e:
                print(f"Warning: Could not load cache for {metadata_file}: {e}")

    def _save_metadata_to_disk(self, metadata: ModelMetadata):
        """Save model metadata to disk"""
        metadata_file = self.metadata_dir / f"{metadata.model_id}.json"
        metadata_dict = {
            'model_id': metadata.model_id,
            'model_name': metadata.model_name,
            'model_type': metadata.model_type,
            'model_version': metadata.model_version,
            'forecasting_category': metadata.forecasting_category,
            'training_timestamp': metadata.training_timestamp,
            'training_dataset_range': metadata.training_dataset_range,
            'features_used': metadata.features_used,
            'parameters': metadata.parameters,
            'evaluation_metrics': metadata.evaluation_metrics,
            'feature_importance': metadata.feature_importance,
            'model_artifact_path': metadata.model_artifact_path,
            'registration_timestamp': metadata.registration_timestamp,
            'model_status': metadata.model_status.value,
            'model_description': metadata.model_description
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)

        # Update cache
        self._cache[metadata.model_id] = metadata_dict

    def register_model(self, metadata: ModelMetadata) -> bool:
        """
        Register a new model in the registry

        Args:
            metadata: Model metadata to register

        Returns:
            True if registration successful, False if model already exists
        """
        # Check if model already exists
        if metadata.model_id in self._cache:
            # Check if this is a version bump or completely new model
            existing_metadata = self._cache[metadata.model_id]
            if existing_metadata.get('model_version') == metadata.model_version:
                # Same version, don't overwrite
                return False

        # Save metadata to disk
        self._save_metadata_to_disk(metadata)

        # Update cache
        self._cache[metadata.model_id] = {
            'model_id': metadata.model_id,
            'model_name': metadata.model_name,
            'model_type': metadata.model_type,
            'model_version': metadata.model_version,
            'forecasting_category': metadata.forecasting_category,
            'training_timestamp': metadata.training_timestamp,
            'training_dataset_range': metadata.training_dataset_range,
            'features_used': metadata.features_used,
            'parameters': metadata.parameters,
            'evaluation_metrics': metadata.evaluation_metrics,
            'feature_importance': metadata.feature_importance,
            'model_artifact_path': metadata.model_artifact_path,
            'registration_timestamp': metadata.registration_timestamp,
            'model_status': metadata.model_status.value,
            'model_description': metadata.model_description
        }

        return True

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """
        Retrieve model metadata by ID

        Args:
            model_id: Unique identifier for the model

        Returns:
            ModelMetadata object or None if not found
        """
        # Check cache first
        if model_id in self._cache:
            metadata_dict = self._cache[model_id]
            return ModelMetadata(
                model_id=metadata_dict['model_id'],
                model_name=metadata_dict['model_name'],
                model_type=metadata_dict['model_type'],
                model_version=metadata_dict['model_version'],
                forecasting_category=metadata_dict['forecasting_category'],
                training_timestamp=metadata_dict['training_timestamp'],
                training_dataset_range=metadata_dict['training_dataset_range'],
                features_used=metadata_dict['features_used'],
                parameters=metadata_dict['parameters'],
                evaluation_metrics=metadata_dict['evaluation_metrics'],
                feature_importance=metadata_dict['feature_importance'],
                model_artifact_path=metadata_dict['model_artifact_path'],
                registration_timestamp=metadata_dict['registration_timestamp'],
                model_status=ModelLifecycleState(metadata_dict['model_status']),
                model_description=metadata_dict['model_description']
            )

        # Load from disk if not cached
        metadata_file = self.metadata_dir / f"{model_id}.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)

                # Cache it
                self._cache[model_id] = metadata_dict

                return ModelMetadata(
                    model_id=metadata_dict['model_id'],
                    model_name=metadata_dict['model_name'],
                    model_type=metadata_dict['model_type'],
                    model_version=metadata_dict['model_version'],
                    forecasting_category=metadata_dict['forecasting_category'],
                    training_timestamp=metadata_dict['training_timestamp'],
                    training_dataset_range=metadata_dict['training_dataset_range'],
                    features_used=metadata_dict['features_used'],
                    parameters=metadata_dict['parameters'],
                    evaluation_metrics=metadata_dict['evaluation_metrics'],
                    feature_importance=metadata_dict['feature_importance'],
                    model_artifact_path=metadata_dict['model_artifact_path'],
                    registration_timestamp=metadata_dict['registration_timestamp'],
                    model_status=ModelLifecycleState(metadata_dict['model_status']),
                    model_description=metadata_dict['model_description']
                )
            except Exception as e:
                print(f"Error loading model {model_id}: {e}")
                return None

        return None

    def list_models(self) -> List[ModelMetadata]:
        """
        List all registered models

        Returns:
            List of ModelMetadata objects
        """
        models = []
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                model = self.get_model(metadata_file.stem)
                if model:
                    models.append(model)
            except Exception as e:
                print(f"Error loading model {metadata_file.stem}: {e}")
                continue
        return models

    def get_model_versions(self, model_id: str) -> List[str]:
        """
        Get all versions of a specific model

        Args:
            model_id: Unique identifier for the model

        Returns:
            List of version strings
        """
        # This is a simplified implementation - in a real system we'd maintain version history
        model = self.get_model(model_id)
        if model:
            return [model.model_version]
        return []

    def update_model_status(self, model_id: str, status: ModelLifecycleState) -> bool:
        """
        Update the lifecycle status of a model

        Args:
            model_id: Unique identifier for the model
            status: New lifecycle status

        Returns:
            True if successful, False otherwise
        """
        model = self.get_model(model_id)
        if model:
            model.model_status = status
            self._save_metadata_to_disk(model)
            return True
        return False

    def get_production_model(self, forecasting_category: str) -> Optional[ModelMetadata]:
        """
        Get the currently production model for a forecasting category

        Args:
            forecasting_category: Category to search for

        Returns:
            Production model metadata or None
        """
        models = self.list_models()
        for model in models:
            if (model.model_status == ModelLifecycleState.PRODUCTION and
                model.forecasting_category == forecasting_category):
                return model
        return None

    def get_candidate_models(self) -> List[ModelMetadata]:
        """
        Get all candidate models ready for promotion

        Returns:
            List of candidate model metadata
        """
        models = self.list_models()
        return [model for model in models if model.model_status == ModelLifecycleState.CANDIDATE]

    def save_promotion_decision(self, decision: PromotionDecision) -> None:
        """
        Save a promotion decision to history

        Args:
            decision: Promotion decision to save
        """
        decision_file = self.promotion_history_dir / f"{decision.model_id}_{decision.model_version}.json"
        decision_dict = {
            'model_id': decision.model_id,
            'model_version': decision.model_version,
            'previous_production_version': decision.previous_production_version,
            'promotion_reason': decision.promotion_reason,
            'evaluation_results': decision.evaluation_results,
            'decision_timestamp': decision.decision_timestamp,
            'approved': decision.approved
        }

        with open(decision_file, 'w') as f:
            json.dump(decision_dict, f, indent=2)

    def save_rollback_record(self, rollback_record: RollbackRecord) -> None:
        """
        Save a rollback record to history

        Args:
            rollback_record: Rollback record to save
        """
        rollback_file = self.rollback_history_dir / f"{rollback_record.model_id}_{rollback_record.rollback_timestamp}.json"
        rollback_dict = {
            'model_id': rollback_record.model_id,
            'rolled_back_from_version': rollback_record.rolled_back_from_version,
            'rolled_back_to_version': rollback_record.rolled_back_to_version,
            'rollback_reason': rollback_record.rollback_reason,
            'rollback_timestamp': rollback_record.rollback_timestamp,
            'rollback_user': rollback_record.rollback_user
        }

        with open(rollback_file, 'w') as f:
            json.dump(rollback_dict, f, indent=2)

    def get_promotion_history(self, model_id: str) -> List[PromotionDecision]:
        """
        Get promotion history for a model

        Args:
            model_id: Model identifier

        Returns:
            List of promotion decisions
        """
        decisions = []
        for history_file in self.promotion_history_dir.glob(f"{model_id}_*.json"):
            try:
                with open(history_file, 'r') as f:
                    decision_dict = json.load(f)
                    decision = PromotionDecision(
                        model_id=decision_dict['model_id'],
                        model_version=decision_dict['model_version'],
                        previous_production_version=decision_dict['previous_production_version'],
                        promotion_reason=decision_dict['promotion_reason'],
                        evaluation_results=decision_dict['evaluation_results'],
                        decision_timestamp=decision_dict['decision_timestamp'],
                        approved=decision_dict['approved']
                    )
                    decisions.append(decision)
            except Exception as e:
                print(f"Error loading promotion history {history_file}: {e}")
                continue
        return decisions

    def get_rollback_history(self, model_id: str) -> List[RollbackRecord]:
        """
        Get rollback history for a model

        Args:
            model_id: Model identifier

        Returns:
            List of rollback records
        """
        records = []
        for history_file in self.rollback_history_dir.glob(f"{model_id}_*.json"):
            try:
                with open(history_file, 'r') as f:
                    record_dict = json.load(f)
                    record = RollbackRecord(
                        model_id=record_dict['model_id'],
                        rolled_back_from_version=record_dict['rolled_back_from_version'],
                        rolled_back_to_version=record_dict['rolled_back_to_version'],
                        rollback_reason=record_dict['rollback_reason'],
                        rollback_timestamp=record_dict['rollback_timestamp'],
                        rollback_user=record_dict['rollback_user']
                    )
                    records.append(record)
            except Exception as e:
                print(f"Error loading rollback history {history_file}: {e}")
                continue
        return records