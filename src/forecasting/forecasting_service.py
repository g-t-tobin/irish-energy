"""
Forecasting service for generating predictions
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from src.forecasting.models import ForecastResult, ModelMetadata, ModelEvaluationResult
from src.forecasting.features import FeatureEngineer
from src.forecasting.training import MLForecastModel
from src.forecasting.baselines import BaselineForecaster
import joblib
import os
from src.common.runtime_paths import writable_runtime_dir

class ForecastingService:
    """Main service for forecasting operations"""

    def __init__(self, model_dir: str = "./models"):
        model_dir = writable_runtime_dir(model_dir)
        self.model_dir = model_dir
        self.feature_engineer = FeatureEngineer()
        self.baseline_forecaster = BaselineForecaster()
        os.makedirs(model_dir, exist_ok=True)

    def generate_forecast(self,
                         model: MLForecastModel,
                         data: pd.DataFrame,
                         forecast_horizon: int = 1,
                         forecast_date: Optional[str] = None) -> ForecastResult:
        """
        Generate a forecast using a trained model

        Args:
            model: Trained forecasting model
            data: Historical data for feature engineering
            forecast_horizon: Number of periods to forecast
            forecast_date: Date for the forecast (defaults to today)

        Returns:
            ForecastResult with prediction
        """
        # Get the most recent data point
        if data.empty:
            raise ValueError("No data provided for forecasting")

        # Engineer features for the latest data point
        latest_data = data.tail(1).copy()
        features_df = self.feature_engineer.engineer_features(latest_data)
        features_for_pred = self.feature_engineer.prepare_features_for_prediction(features_df)

        # Make prediction
        predictions = model.predict(features_for_pred)

        # Create forecast result
        forecast_timestamp = forecast_date or datetime.now().isoformat()
        predicted_demand = float(predictions.iloc[0]) if len(predictions) > 0 else 0.0

        return ForecastResult(
            forecast_timestamp=forecast_timestamp,
            predicted_demand_mw=predicted_demand,
            forecast_horizon_days=forecast_horizon,
            model_identifier=model.identifier,
            model_version=model.version,
            generation_timestamp=datetime.now().isoformat(),
            metadata={
                'model_type': model.model_type,
                'forecast_horizon': forecast_horizon
            }
        )

    def generate_baseline_forecast(self,
                                  data: pd.DataFrame,
                                  forecast_method: str = 'persistence',
                                  forecast_horizon: int = 1) -> ForecastResult:
        """
        Generate forecast using baseline method

        Args:
            data: Historical data
            forecast_method: Method to use ('persistence', 'seasonal_naive', etc.)
            forecast_horizon: Number of periods to forecast

        Returns:
            ForecastResult with prediction
        """
        if data.empty:
            raise ValueError("No data provided for forecasting")

        # Choose forecast method
        if forecast_method == 'persistence':
            forecast = self.baseline_forecaster.persistence_forecast(data, forecast_horizon)
        elif forecast_method == 'seasonal_naive':
            forecast = self.baseline_forecaster.seasonal_naive_forecast(data, forecast_horizon)
        elif forecast_method == 'moving_average':
            forecast = self.baseline_forecaster.moving_average_forecast(data, 7, forecast_horizon)
        elif forecast_method == 'statistical_baseline':
            forecast = self.baseline_forecaster.statistical_baseline_forecast(data, forecast_horizon)
        else:
            raise ValueError(f"Unknown forecast method: {forecast_method}")

        # Create forecast result
        predicted_demand = float(forecast.iloc[0]) if len(forecast) > 0 else 0.0

        return ForecastResult(
            forecast_timestamp=datetime.now().isoformat(),
            predicted_demand_mw=predicted_demand,
            forecast_horizon_days=forecast_horizon,
            model_identifier=f"baseline_{forecast_method}",
            model_version="1.0",
            generation_timestamp=datetime.now().isoformat(),
            metadata={
                'method': forecast_method,
                'forecast_horizon': forecast_horizon
            }
        )

    def save_model(self, model: MLForecastModel, model_name: str) -> str:
        """
        Save a trained model to disk

        Args:
            model: Trained model to save
            model_name: Name for the saved model

        Returns:
            Path to saved model file
        """
        filename = f"{model_name}.joblib"
        filepath = os.path.join(self.model_dir, filename)
        model.save_model(filepath)
        return filepath

    def load_model(self, model_name: str) -> MLForecastModel:
        """
        Load a trained model from disk

        Args:
            model_name: Name of the model to load

        Returns:
            Loaded MLForecastModel instance
        """
        filename = f"{model_name}.joblib"
        filepath = os.path.join(self.model_dir, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        # Create a new model instance and load it
        model = MLForecastModel(
            identifier="loaded_model",
            model_type="unknown",
            parameters={}
        )
        model.load_model(filepath)
        return model

    def compare_models(self,
                      data: pd.DataFrame,
                      models: List[MLForecastModel],
                      test_period_start: str,
                      test_period_end: str,
                      forecast_horizon: int = 1) -> Dict[str, ModelEvaluationResult]:
        """
        Compare multiple models on test data

        Args:
            data: Complete dataset
            models: List of models to compare
            test_period_start: Start of test period
            test_period_end: End of test period
            forecast_horizon: Forecast horizon

        Returns:
            Dictionary of evaluation results for each model
        """
        # Split data into train/test
        train_data = data[data['timestamp'] < test_period_start]
        test_data = data[(data['timestamp'] >= test_period_start) & (data['timestamp'] <= test_period_end)]

        if len(test_data) < forecast_horizon:
            raise ValueError("Insufficient test data for model comparison")

        results = {}

        # For each model, train and evaluate
        for model in models:
            # Engineer features
            train_features = self.feature_engineer.engineer_features(train_data)
            X_train = train_features[self.feature_engineer.get_feature_columns()]
            y_train = train_features['demand_mw']

            test_features = self.feature_engineer.engineer_features(test_data)
            X_test = test_features[self.feature_engineer.get_feature_columns()]
            y_test = test_features['demand_mw']

            # Train model
            model.train(X_train, y_train)

            # Evaluate model
            metrics = model.evaluate(X_test, y_test)

            # Create evaluation result
            eval_result = ModelEvaluationResult(
                model_identifier=model.identifier,
                model_version=model.version,
                forecast_horizon_days=forecast_horizon,
                training_period=(str(train_data['timestamp'].min()), str(train_data['timestamp'].max())),
                evaluation_period=(test_period_start, test_period_end),
                observation_count=len(y_test),
                metrics=metrics,
                baseline_comparison={},
                limitations=[],
                seasonal_performance={}
            )

            results[model.identifier] = eval_result

        return results