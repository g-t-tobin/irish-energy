"""
Forecasting models for Irish Energy Analytics Data Platform
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

@dataclass
class ForecastResult:
    """Result of forecasting operation"""
    forecast_timestamp: str
    predicted_demand_mw: float
    forecast_horizon_days: int
    model_identifier: str
    model_version: str
    generation_timestamp: str
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.generation_timestamp is None:
            self.generation_timestamp = datetime.now().isoformat()

@dataclass
class ModelEvaluationResult:
    """Result of model evaluation"""
    model_identifier: str
    model_version: str
    forecast_horizon_days: int
    training_period: Tuple[str, str]
    evaluation_period: Tuple[str, str]
    observation_count: int
    metrics: Dict[str, float]
    baseline_comparison: Dict[str, float]
    limitations: List[str]
    seasonal_performance: Dict[str, Dict[str, float]]

    def __post_init__(self):
        if self.training_period is None:
            self.training_period = ("unknown", "unknown")
        if self.evaluation_period is None:
            self.evaluation_period = ("unknown", "unknown")
        if self.metrics is None:
            self.metrics = {}
        if self.baseline_comparison is None:
            self.baseline_comparison = {}
        if self.limitations is None:
            self.limitations = []
        if self.seasonal_performance is None:
            self.seasonal_performance = {}

@dataclass
class ModelMetadata:
    """Metadata for trained models"""
    model_identifier: str
    model_version: str
    training_timestamp: str
    training_dataset_range: Tuple[str, str]
    features_used: List[str]
    parameters: Dict[str, Any]
    evaluation_metrics: Dict[str, float]
    feature_importance: Dict[str, float]

    def __post_init__(self):
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
class ForecastModel:
    """Generic forecasting model interface"""
    identifier: str
    version: str
    model_type: str
    parameters: Dict[str, Any]
    metadata: ModelMetadata

    def predict(self, features: pd.DataFrame) -> pd.Series:
        """Make predictions using the model"""
        raise NotImplementedError("Subclasses must implement predict method")

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Train the model"""
        raise NotImplementedError("Subclasses must implement train method")

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate the model"""
        raise NotImplementedError("Subclasses must implement evaluate method")