"""
Model versioning and artifact management for MLOps framework
"""

import json
import os
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from src.mlops.models import ModelMetadata
from src.forecasting.models import ForecastModel
from src.forecasting.renewable_models import RenewableForecastModel
import joblib

class ModelVersioning:
    """Manage model versions and artifacts"""

    def __init__(self, artifacts_dir: str = "./model_artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_model_artifact(self, model: ForecastModel, metadata: ModelMetadata) -> str:
        """
        Save a trained model artifact to disk

        Args:
            model: Trained model to save
            metadata: Model metadata

        Returns:
            Path to saved artifact
        """
        # Create artifact path based on model ID and version
        artifact_path = self.artifacts_dir / metadata.model_id / metadata.model_version
        artifact_path.mkdir(parents=True, exist_ok=True)

        # Save model using joblib
        model_file = artifact_path / "model.joblib"
        model.save_model(str(model_file))

        # Save metadata alongside model
        metadata_file = artifact_path / "metadata.json"
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
            'model_artifact_path': str(artifact_path),
            'registration_timestamp': metadata.registration_timestamp,
            'model_status': metadata.model_status.value,
            'model_description': metadata.model_description
        }

        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)

        return str(artifact_path)

    def load_model_artifact(self, model_id: str, version: str) -> Optional[ForecastModel]:
        """
        Load a model artifact from disk

        Args:
            model_id: Model identifier
            version: Model version

        Returns:
            Loaded model or None if not found
        """
        artifact_path = self.artifacts_dir / model_id / version
        model_file = artifact_path / "model.joblib"

        if model_file.exists():
            # This is a simplified approach - in reality, we'd need to reconstruct
            # the model based on its type, but for now we'll just return a generic model
            # In a real implementation, we'd need to know the model type to load it properly
            return None  # Placeholder - real implementation would reconstruct model

        return None

    def list_model_versions(self, model_id: str) -> List[str]:
        """
        List all versions of a specific model

        Args:
            model_id: Model identifier

        Returns:
            List of version strings
        """
        model_dir = self.artifacts_dir / model_id
        if model_dir.exists():
            versions = []
            for item in model_dir.iterdir():
                if item.is_dir():
                    versions.append(item.name)
            return sorted(versions)
        return []

    def delete_model_version(self, model_id: str, version: str) -> bool:
        """
        Delete a specific model version

        Args:
            model_id: Model identifier
            version: Model version to delete

        Returns:
            True if successful, False otherwise
        """
        artifact_path = self.artifacts_dir / model_id / version
        if artifact_path.exists():
            try:
                shutil.rmtree(artifact_path)
                return True
            except Exception as e:
                print(f"Error deleting model version {model_id}/{version}: {e}")
                return False
        return False

    def get_model_artifact_path(self, model_id: str, version: str) -> Optional[str]:
        """
        Get the artifact path for a specific model version

        Args:
            model_id: Model identifier
            version: Model version

        Returns:
            Artifact path or None if not found
        """
        artifact_path = self.artifacts_dir / model_id / version
        if artifact_path.exists():
            return str(artifact_path)
        return None

class ModelPersistence:
    """Handle model persistence operations"""

    def __init__(self, artifacts_dir: str = "./model_artifacts", metadata_dir: str = "./model_registry/metadata"):
        self.versioning = ModelVersioning(artifacts_dir)
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_model_metadata(self, metadata: ModelMetadata) -> None:
        """
        Save model metadata to persistent storage

        Args:
            metadata: Model metadata to save
        """
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

    def load_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """
        Load model metadata from persistent storage

        Args:
            model_id: Model identifier

        Returns:
            ModelMetadata object or None if not found
        """
        metadata_file = self.metadata_dir / f"{model_id}.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)

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
                    model_status=metadata_dict['model_status'],
                    model_description=metadata_dict['model_description']
                )
            except Exception as e:
                print(f"Error loading model metadata {model_id}: {e}")
                return None
        return None