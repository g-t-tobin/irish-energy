"""
Renewable energy forecasting service
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.forecasting.renewable_models import RenewableForecastResult, RenewableModelMetadata
from src.forecasting.renewable_features import RenewableFeatureEngineer
from src.forecasting.wind_forecasting import WindForecaster
from src.forecasting.solar_forecasting import SolarForecaster
from src.forecasting.renewable_models import RenewableForecastModel
from src.forecasting.baselines import BaselineForecaster
import joblib
import os
from src.common.runtime_paths import writable_runtime_dir

class RenewableForecastingService:
    """Main service for renewable forecasting operations"""

    def __init__(self, model_dir: str = "./renewable_models"):
        model_dir = writable_runtime_dir(model_dir)
        self.model_dir = model_dir
        self.feature_engineer = RenewableFeatureEngineer()
        self.wind_forecaster = WindForecaster()
        self.solar_forecaster = SolarForecaster()
        self.baseline_forecaster = BaselineForecaster()
        os.makedirs(model_dir, exist_ok=True)

    def generate_wind_forecast(self,
                              data: pd.DataFrame,
                              forecast_horizon: int = 1,
                              forecast_method: str = 'persistence') -> RenewableForecastResult:
        """
        Generate wind generation forecast

        Args:
            data: Historical generation data
            forecast_horizon: Number of periods to forecast
            forecast_method: Method to use ('persistence', 'seasonal_naive', 'moving_average', 'statistical_baseline')

        Returns:
            RenewableForecastResult with prediction
        """
        if data.empty:
            raise ValueError("No data provided for forecasting")

        # Choose forecast method
        if forecast_method == 'persistence':
            forecast = self.wind_forecaster.persistence_forecast(data, forecast_horizon)
        elif forecast_method == 'seasonal_naive':
            forecast = self.wind_forecaster.seasonal_naive_forecast(data, forecast_horizon)
        elif forecast_method == 'moving_average':
            forecast = self.wind_forecaster.moving_average_forecast(data, 7, forecast_horizon)
        elif forecast_method == 'statistical_baseline':
            forecast = self.wind_forecaster.statistical_baseline_forecast(data, forecast_horizon)
        else:
            raise ValueError(f"Unknown forecast method: {forecast_method}")

        # Create forecast result
        predicted_generation = float(forecast.iloc[0]) if len(forecast) > 0 else 0.0

        return RenewableForecastResult(
            forecast_timestamp=datetime.now().isoformat(),
            predicted_generation_mw=predicted_generation,
            forecast_horizon_days=forecast_horizon,
            model_identifier=f"wind_{forecast_method}",
            model_version="1.0",
            generation_category="wind",
            generation_timestamp=data['timestamp'].iloc[-1].isoformat() if not data.empty else datetime.now().isoformat(),
            generation_unit="MW",
            metadata={
                'method': forecast_method,
                'forecast_horizon': forecast_horizon
            }
        )

    def generate_solar_forecast(self,
                               data: pd.DataFrame,
                               forecast_horizon: int = 1,
                               forecast_method: str = 'persistence') -> RenewableForecastResult:
        """
        Generate solar generation forecast

        Args:
            data: Historical generation data
            forecast_horizon: Number of periods to forecast
            forecast_method: Method to use ('persistence', 'seasonal_naive', 'moving_average', 'statistical_baseline')

        Returns:
            RenewableForecastResult with prediction
        """
        if data.empty:
            raise ValueError("No data provided for forecasting")

        # Choose forecast method
        if forecast_method == 'persistence':
            forecast = self.solar_forecaster.persistence_forecast(data, forecast_horizon)
        elif forecast_method == 'seasonal_naive':
            forecast = self.solar_forecaster.seasonal_naive_forecast(data, forecast_horizon)
        elif forecast_method == 'moving_average':
            forecast = self.solar_forecaster.moving_average_forecast(data, 7, forecast_horizon)
        elif forecast_method == 'statistical_baseline':
            forecast = self.solar_forecaster.statistical_baseline_forecast(data, forecast_horizon)
        else:
            raise ValueError(f"Unknown forecast method: {forecast_method}")

        # Create forecast result
        predicted_generation = float(forecast.iloc[0]) if len(forecast) > 0 else 0.0

        return RenewableForecastResult(
            forecast_timestamp=datetime.now().isoformat(),
            predicted_generation_mw=predicted_generation,
            forecast_horizon_days=forecast_horizon,
            model_identifier=f"solar_{forecast_method}",
            model_version="1.0",
            generation_category="solar",
            generation_timestamp=data['timestamp'].iloc[-1].isoformat() if not data.empty else datetime.now().isoformat(),
            generation_unit="MW",
            metadata={
                'method': forecast_method,
                'forecast_horizon': forecast_horizon
            }
        )

    def generate_renewable_total_forecast(self,
                                         data: pd.DataFrame,
                                         forecast_horizon: int = 1,
                                         forecast_method: str = 'persistence') -> RenewableForecastResult:
        """
        Generate total renewable generation forecast

        Args:
            data: Historical generation data
            forecast_horizon: Number of periods to forecast
            forecast_method: Method to use ('persistence', 'seasonal_naive', 'moving_average', 'statistical_baseline')

        Returns:
            RenewableForecastResult with prediction
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
        predicted_generation = float(forecast.iloc[0]) if len(forecast) > 0 else 0.0

        return RenewableForecastResult(
            forecast_timestamp=datetime.now().isoformat(),
            predicted_generation_mw=predicted_generation,
            forecast_horizon_days=forecast_horizon,
            model_identifier=f"renewable_total_{forecast_method}",
            model_version="1.0",
            generation_category="renewable_total",
            generation_timestamp=data['timestamp'].iloc[-1].isoformat() if not data.empty else datetime.now().isoformat(),
            generation_unit="MW",
            metadata={
                'method': forecast_method,
                'forecast_horizon': forecast_horizon
            }
        )

    def save_model(self, model: RenewableForecastModel, model_name: str) -> str:
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

    def load_model(self, model_name: str) -> RenewableForecastModel:
        """
        Load a trained model from disk

        Args:
            model_name: Name of the model to load

        Returns:
            Loaded RenewableForecastModel instance
        """
        filename = f"{model_name}.joblib"
        filepath = os.path.join(self.model_dir, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")

        # Create a new model instance and load it
        model = RenewableForecastModel(
            identifier="loaded_model",
            model_type="unknown",
            generation_category="unknown",
            parameters={}
        )
        model.load_model(filepath)
        return model

    def compare_models(self,
                       data: pd.DataFrame,
                       models: List[RenewableForecastModel],
                       test_period_start: str,
                       test_period_end: str,
                       forecast_horizon: int = 1) -> Dict[str, Any]:
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
            y_train = train_features['renewable_generation_mw']

            test_features = self.feature_engineer.engineer_features(test_data)
            X_test = test_features[self.feature_engineer.get_feature_columns()]
            y_test = test_features['renewable_generation_mw']

            # Train model
            model.train(X_train, y_train)

            # Evaluate model
            metrics = model.evaluate(X_test, y_test)

            # Create evaluation result
            eval_result = {
                'model_identifier': model.identifier,
                'model_version': model.version,
                'forecast_horizon_days': forecast_horizon,
                'training_period': (str(train_data['timestamp'].min()), str(train_data['timestamp'].max())),
                'evaluation_period': (test_period_start, test_period_end),
                'observation_count': len(y_test),
                'metrics': metrics,
                'baseline_comparison': {},
                'limitations': [],
                'seasonal_performance': {}
            }

            results[model.identifier] = eval_result

        return results