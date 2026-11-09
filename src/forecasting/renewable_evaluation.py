"""
Renewable energy evaluation and backtesting
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from src.forecasting.models import ModelEvaluationResult
from src.forecasting.renewable_features import RenewableFeatureEngineer
from src.forecasting.evaluation import ModelEvaluator
import warnings

class RenewableModelEvaluator:
    """Evaluate renewable forecasting models"""

    def __init__(self):
        self.feature_engineer = RenewableFeatureEngineer()
        self.evaluator = ModelEvaluator()

    def evaluate_model(self, model, X_test: pd.DataFrame, y_test: pd.Series,
                      model_name: str, forecast_horizon: int = 1,
                      generation_category: str = "renewable_total") -> Dict[str, Any]:
        """
        Evaluate a single renewable model

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test targets
            model_name: Name of the model
            forecast_horizon: Forecast horizon
            generation_category: Type of generation ('wind', 'solar', 'renewable_total')

        Returns:
            Model evaluation result
        """
        # Make predictions
        predictions = model.predict(X_test)

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

        metrics = {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'smape': smape,
            'mbe': mbe
        }

        return {
            'model_identifier': model_name,
            'model_version': "1.0",
            'forecast_horizon_days': forecast_horizon,
            'training_period': ("unknown", "unknown"),
            'evaluation_period': ("unknown", "unknown"),
            'observation_count': len(y_test),
            'metrics': metrics,
            'baseline_comparison': {},
            'limitations': [],
            'seasonal_performance': {},
            'generation_category': generation_category
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

class RenewableBacktester:
    """Perform chronological backtesting for renewable forecasting models"""

    def __init__(self):
        self.evaluator = RenewableModelEvaluator()

    def rolling_origin_backtest(self, data: pd.DataFrame,
                               model_class,
                               feature_engineer: RenewableFeatureEngineer,
                               train_window: int,
                               forecast_horizon: int,
                               test_size: int = 30,
                               generation_category: str = "renewable_total") -> Dict[str, Any]:
        """
        Perform rolling origin backtesting for renewable models

        Args:
            data: Complete dataset
            model_class: Class of model to train
            feature_engineer: Feature engineer instance
            train_window: Size of training window in days
            forecast_horizon: Forecast horizon in days
            test_size: Number of test periods to evaluate
            generation_category: Type of generation ('wind', 'solar', 'renewable_total')

        Returns:
            Dictionary with backtesting results
        """
        if len(data) < train_window + forecast_horizon + test_size:
            raise ValueError("Insufficient data for backtesting")

        # Initialize results
        all_results = []
        model_metadata_list = []

        # Perform backtesting
        for i in range(test_size):
            # Define test period
            test_start_idx = len(data) - test_size + i
            test_end_idx = test_start_idx + forecast_horizon

            if test_end_idx > len(data):
                break

            # Define training period
            train_end_idx = test_start_idx - forecast_horizon
            if train_end_idx < train_window:
                continue

            train_start_idx = max(0, train_end_idx - train_window)

            # Extract data segments
            train_data = data.iloc[train_start_idx:train_end_idx]
            test_data = data.iloc[test_start_idx:test_end_idx]

            # Engineer features for training
            train_features = feature_engineer.engineer_features(train_data, generation_category=generation_category)
            X_train = train_features[feature_engineer.get_feature_columns()]
            y_train = train_features['renewable_generation_mw']

            # Engineer features for testing
            test_features = feature_engineer.engineer_features(test_data, generation_category=generation_category)
            X_test = test_features[feature_engineer.get_feature_columns()]
            y_test = test_features['renewable_generation_mw']

            # Skip if no features
            if X_train.empty or X_test.empty:
                continue

            # Train model
            model = model_class()
            model.train(X_train, y_train)

            # Evaluate model
            eval_result = self.evaluator.evaluate_model(
                model, X_test, y_test,
                model_class.__name__,
                forecast_horizon,
                generation_category
            )

            # Store results
            all_results.append(eval_result)

            # Store model metadata
            model_metadata = {
                'model': model,
                'train_period': (train_data['timestamp'].min(), train_data['timestamp'].max()),
                'test_period': (test_data['timestamp'].min(), test_data['timestamp'].max()),
                'evaluation': eval_result
            }
            model_metadata_list.append(model_metadata)

        # Aggregate results
        aggregated_metrics = self._aggregate_backtest_results(all_results)

        return {
            'results': all_results,
            'model_metadata': model_metadata_list,
            'aggregated_metrics': aggregated_metrics,
            'generation_category': generation_category
        }

    def _aggregate_backtest_results(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate results from multiple backtest periods"""
        if not results:
            return {}

        # Calculate average metrics across all test periods
        metrics_sum = {}
        for result in results:
            for metric_name, value in result['metrics'].items():
                if metric_name not in metrics_sum:
                    metrics_sum[metric_name] = 0
                metrics_sum[metric_name] += value

        # Calculate averages
        avg_metrics = {metric: total / len(results) for metric, total in metrics_sum.items()}
        return avg_metrics