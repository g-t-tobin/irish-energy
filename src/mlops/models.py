"""
MLOps framework for managing forecasting models throughout their lifecycle
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import uuid
from pathlib import Path
from abc import ABC, abstractmethod

# Import forecasting models for type annotations
from src.forecasting.models import ForecastResult, ModelEvaluationResult
from src.forecasting.renewable_models import RenewableForecastResult
from src.forecasting.renewable_models import RenewableModelMetadata

# Import existing model interfaces
from src.forecasting.models import ForecastModel
from src.forecasting.renewable_models import RenewableForecastModel

# Import existing evaluation metrics
from src.forecasting.evaluation import ModelEvaluator
from src.forecasting.renewable_evaluation import RenewableModelEvaluator


class ModelLifecycleState(Enum):
    """Enumeration of model lifecycle states"""
    REGISTERED = "registered"
    TRAINING = "training"
    EVALUATING = "evaluating"
    CANDIDATE = "candidate"
    PRODUCTION = "production"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass
class ModelMetadata:
    """Metadata for registered forecasting models"""
    model_id: str
    model_name: str
    model_type: str
    model_version: str
    forecasting_category: str  # demand, renewable_total, wind, solar
    training_timestamp: str
    training_dataset_range: Tuple[str, str]
    features_used: List[str]
    parameters: Dict[str, Any]
    evaluation_metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    model_artifact_path: str
    registration_timestamp: str
    model_status: ModelLifecycleState = ModelLifecycleState.REGISTERED
    model_description: str = ""

    def __post_init__(self):
        if self.registration_timestamp is None:
            self.registration_timestamp = datetime.now().isoformat()
        if self.training_timestamp is None:
            self.training_timestamp = datetime.now().isoformat()
        if self.training_dataset_range is None:
            self.training_dataset_range = ("unknown", "unknown")
        if self.features_used is None:
            self.features_used = []
        if self.parameters is None:
            self.parameters = {}
        if self.evaluation_metrics is None:
            self.evaluation_metrics = {}
        if self.feature_importance is None:
            self.feature_importance = {}


@dataclass
class ModelPerformance:
    """Performance tracking for models"""
    model_id: str
    model_version: str
    evaluation_period: Tuple[str, str]
    forecast_horizon: int
    observation_count: int
    metrics: Dict[str, float]
    evaluation_timestamp: str

    def __post_init__(self):
        if self.evaluation_timestamp is None:
            self.evaluation_timestamp = datetime.now().isoformat()


@dataclass
class DriftDetectionResult:
    """Results from drift detection analysis"""
    feature_name: str
    drift_detected: bool
    drift_score: float
    drift_type: str  # distribution_change, missing_values, outliers
    previous_distribution: Dict[str, float]
    current_distribution: Dict[str, float]
    timestamp: str

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class RetrainingRecommendation:
    """Recommendation for model retraining"""
    model_id: str
    model_version: str
    recommendation_reason: str
    recommendation_type: str  # performance_degradation, data_drift, model_age
    confidence_score: float
    suggested_action: str  # retrain, monitor, investigate
    threshold_met: bool
    timestamp: str

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class PromotionDecision:
    """Model promotion decision record"""
    model_id: str
    model_version: str
    previous_production_version: Optional[str]
    promotion_reason: str
    evaluation_results: Dict[str, Any]
    decision_timestamp: str
    approved: bool

    def __post_init__(self):
        if self.decision_timestamp is None:
            self.decision_timestamp = datetime.now().isoformat()


@dataclass
class RollbackRecord:
    """Record of model rollback events"""
    model_id: str
    rolled_back_from_version: str
    rolled_back_to_version: str
    rollback_reason: str
    rollback_timestamp: str
    rollback_user: Optional[str] = None

    def __post_init__(self):
        if self.rollback_timestamp is None:
            self.rollback_timestamp = datetime.now().isoformat()