"""
Machine learning models for forecasting
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from src.forecasting.models import ForecastModel, ModelEvaluationResult
import joblib
import os

class MLForecastModel(ForecastModel):
    """Machine learning forecasting model wrapper"""

    def __init__(self, identifier: str, model_type: str, parameters: Dict[str, Any] = None):
        super().__init__(identifier, "1.0", model_type, parameters or {}, None)
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