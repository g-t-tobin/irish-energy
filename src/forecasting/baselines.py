"""
Baseline forecasting models
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from src.forecasting.models import ForecastModel, ModelEvaluationResult

class BaselineForecaster:
    """Implement baseline forecasting models"""

    def __init__(self):
        pass

    def persistence_forecast(self, data: pd.DataFrame, forecast_horizon: int = 1) -> pd.Series:
        """
        Persistence forecast: use the most recent observation

        Args:
            data: DataFrame with demand_mw column
            forecast_horizon: Number of periods to forecast

        Returns:
            Series of forecasts
        """
        if len(data) < forecast_horizon:
            raise ValueError("Not enough data for forecast horizon")

        # Take the last observation as forecast
        last_observation = data['demand_mw'].iloc[-1]
        forecasts = [last_observation] * forecast_horizon
        return pd.Series(forecasts)

    def seasonal_naive_forecast(self, data: pd.DataFrame, forecast_horizon: int = 1) -> pd.Series:
        """
        Seasonal naive forecast: use corresponding previous day/week observation

        Args:
            data: DataFrame with demand_mw column and timestamp
            forecast_horizon: Number of periods to forecast

        Returns:
            Series of forecasts
        """
        if len(data) < 7 + forecast_horizon:
            raise ValueError("Not enough data for seasonal naive forecast")

        # For daily data, use the same day of the previous week
        forecasts = []
        for i in range(forecast_horizon):
            # Get the corresponding day from previous week
            idx = len(data) - 7 - i
            if idx >= 0:
                forecasts.append(data['demand_mw'].iloc[idx])
            else:
                # Fall back to last available value if not enough history
                forecasts.append(data['demand_mw'].iloc[-1])

        return pd.Series(forecasts)

    def moving_average_forecast(self, data: pd.DataFrame, window: int = 7, forecast_horizon: int = 1) -> pd.Series:
        """
        Moving average forecast: use rolling average

        Args:
            data: DataFrame with demand_mw column
            window: Rolling window size
            forecast_horizon: Number of periods to forecast

        Returns:
            Series of forecasts
        """
        if len(data) < window:
            raise ValueError("Not enough data for moving average")

        # Use the rolling average as forecast
        rolling_mean = data['demand_mw'].rolling(window=window, min_periods=1).mean()
        last_average = rolling_mean.iloc[-1]
        forecasts = [last_average] * forecast_horizon
        return pd.Series(forecasts)

    def statistical_baseline_forecast(self, data: pd.DataFrame, forecast_horizon: int = 1) -> pd.Series:
        """
        Statistical baseline using simple methods

        Args:
            data: DataFrame with demand_mw column
            forecast_horizon: Number of periods to forecast

        Returns:
            Series of forecasts
        """
        # For simplicity, use a combination of persistence and moving average
        persistence_forecast = self.persistence_forecast(data, forecast_horizon)
        ma_forecast = self.moving_average_forecast(data, 7, forecast_horizon)

        # Weighted average of baselines
        weights = [0.7, 0.3]  # Persistence gets more weight
        forecasts = (weights[0] * persistence_forecast + weights[1] * ma_forecast)
        return forecasts

    def evaluate_baseline_models(self, data: pd.DataFrame,
                               test_period_start: str,
                               test_period_end: str,
                               forecast_horizon: int = 1) -> Dict[str, ModelEvaluationResult]:
        """
        Evaluate all baseline models

        Args:
            data: Complete dataset
            test_period_start: Start of test period
            test_period_end: End of test period
            forecast_horizon: Number of periods to forecast

        Returns:
            Dictionary of evaluation results
        """
        # Split data into train/test
        train_data = data[data['timestamp'] < test_period_start]
        test_data = data[(data['timestamp'] >= test_period_start) & (data['timestamp'] <= test_period_end)]

        if len(test_data) < forecast_horizon:
            raise ValueError("Insufficient test data for evaluation")

        # Prepare evaluation results
        results = {}

        # Persistence forecast
        persistence_forecast = self.persistence_forecast(train_data, forecast_horizon)
        results['persistence'] = self._evaluate_single_model(
            persistence_forecast,
            test_data['demand_mw'].iloc[:forecast_horizon],
            'persistence',
            forecast_horizon
        )

        # Seasonal naive forecast
        seasonal_forecast = self.seasonal_naive_forecast(train_data, forecast_horizon)
        results['seasonal_naive'] = self._evaluate_single_model(
            seasonal_forecast,
            test_data['demand_mw'].iloc[:forecast_horizon],
            'seasonal_naive',
            forecast_horizon
        )

        # Moving average forecast
        ma_forecast = self.moving_average_forecast(train_data, 7, forecast_horizon)
        results['moving_average'] = self._evaluate_single_model(
            ma_forecast,
            test_data['demand_mw'].iloc[:forecast_horizon],
            'moving_average',
            forecast_horizon
        )

        # Statistical baseline
        stat_forecast = self.statistical_baseline_forecast(train_data, forecast_horizon)
        results['statistical_baseline'] = self._evaluate_single_model(
            stat_forecast,
            test_data['demand_mw'].iloc[:forecast_horizon],
            'statistical_baseline',
            forecast_horizon
        )

        return results

    def _evaluate_single_model(self, predictions: pd.Series,
                             actual: pd.Series,
                             model_name: str,
                             forecast_horizon: int) -> ModelEvaluationResult:
        """
        Evaluate a single model's performance
        """
        if len(predictions) != len(actual):
            raise ValueError("Predictions and actual values must have same length")

        # Calculate metrics
        mae = mean_absolute_error(actual, predictions)
        mse = mean_squared_error(actual, predictions)
        rmse = np.sqrt(mse)

        # Calculate MAPE if actual values are non-zero
        mape = 0.0
        if not actual.eq(0).all():
            mape = mean_absolute_percentage_error(actual, predictions)

        # Calculate sMAPE
        smape = self._calculate_smape(actual, predictions)

        # Calculate mean bias error
        mbe = np.mean(actual - predictions)

        metrics = {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'smape': smape,
            'mbe': mbe
        }

        return ModelEvaluationResult(
            model_identifier=model_name,
            model_version="1.0",
            forecast_horizon_days=forecast_horizon,
            training_period=("unknown", "unknown"),
            evaluation_period=("unknown", "unknown"),
            observation_count=len(actual),
            metrics=metrics,
            baseline_comparison={},
            limitations=[],
            seasonal_performance={}
        )

    def _calculate_smape(self, actual: pd.Series, predicted: pd.Series) -> float:
        """
        Calculate symmetric mean absolute percentage error
        """
        if len(actual) == 0:
            return 0.0

        # Avoid division by zero
        denominator = (np.abs(actual) + np.abs(predicted)) / 2
        nonzero_mask = denominator != 0
        if not nonzero_mask.any():
            return 0.0

        smape = np.mean(np.abs(actual[nonzero_mask] - predicted[nonzero_mask]) / denominator[nonzero_mask]) * 100
        return smape