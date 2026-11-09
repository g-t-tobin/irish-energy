"""
Renewable energy forecasting models for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from src.forecasting.models import ForecastModel, ModelEvaluationResult
from src.forecasting.baselines import BaselineForecaster
import joblib

@dataclass
class RenewableForecastResult:
    """Result of renewable forecasting operation"""
    forecast_timestamp: str
    predicted_generation_mw: float
    forecast_horizon_days: int
    model_identifier: str
    model_version: str
    generation_category: str  # wind, solar, renewable_total
    generation_timestamp: str
    generation_unit: str  # MW
    metadata: Dict[str, Any]

    def __post_init__(self):
        if self.generation_timestamp is None:
            self.generation_timestamp = datetime.now().isoformat()
        if self.generation_unit is None:
            self.generation_unit = "MW"

@dataclass
class RenewableModelMetadata:
    """Metadata for trained renewable models"""
    model_identifier: str
    model_version: str
    generation_category: str
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

class RenewableForecastModel(ForecastModel):
    """Base class for renewable forecasting models"""

    def __init__(self, identifier: str, model_type: str, generation_category: str, parameters: Dict[str, Any] = None):
        super().__init__(identifier, "1.0", model_type, parameters or {}, None)
        self.generation_category = generation_category
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the underlying ML model based on type"""
        if self.model_type == 'linear_regression':
            self.model = LinearRegression(**self.parameters)
        elif self.model_type == 'random_forest':
            self.model = RandomForestRegressor(**self.parameters)
        elif self.model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(**self.parameters)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def predict(self, features: pd.DataFrame) -> pd.Series:
        """Make predictions using the model"""
        if self.model is None:
            raise RuntimeError("Model not initialized")
        predictions = self.model.predict(features)
        # Ensure no negative predictions for generation
        predictions = np.maximum(predictions, 0)
        return pd.Series(predictions, index=features.index)

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Train the model"""
        if self.model is None:
            raise RuntimeError("Model not initialized")
        self.model.fit(X_train, y_train)

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate the model"""
        if self.model is None:
            raise RuntimeError("Model not initialized")

        predictions = self.model.predict(X_test)
        # Ensure no negative predictions for generation
        predictions = np.maximum(predictions, 0)

        # Calculate metrics
        mae = mean_absolute_error(y_test, predictions)
        mse = mean_squared_error(y_test, predictions)
        rmse = np.sqrt(mse)

        # Calculate MAPE if actual values are non-zero
        mape = 0.0
        if not y_test.eq(0).all():
            mape = mean_absolute_percentage_error(y_test, predictions)

        # Calculate sMAPE
        smape = self._calculate_smape(y_test, predictions)

        # Calculate mean bias error
        mbe = np.mean(y_test - predictions)

        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'smape': smape,
            'mbe': mbe
        }

    def _calculate_smape(self, actual: pd.Series, predicted: pd.Series) -> float:
        """Calculate symmetric mean absolute percentage error"""
        if len(actual) == 0:
            return 0.0

        # Avoid division by zero
        denominator = (np.abs(actual) + np.abs(predicted)) / 2
        nonzero_mask = denominator != 0
        if not nonzero_mask.any():
            return 0.0

        smape = np.mean(np.abs(actual[nonzero_mask] - predicted[nonzero_mask]) / denominator[nonzero_mask]) * 100
        return smape

    def save_model(self, filepath: str) -> None:
        """Save the trained model to disk"""
        joblib.dump(self.model, filepath)

    def load_model(self, filepath: str) -> None:
        """Load a trained model from disk"""
        self.model = joblib.load(filepath)