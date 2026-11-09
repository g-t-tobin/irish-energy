"""
Model performance tracking for MLOps framework
"""

import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from src.common.runtime_paths import writable_runtime_dir
from src.mlops.models import ModelPerformance
from src.forecasting.evaluation import ModelEvaluator
from src.forecasting.renewable_evaluation import RenewableModelEvaluator

class ModelPerformanceTracker:
    """Track model performance over time"""

    def __init__(self, performance_dir: str = "./model_performance"):
        performance_dir = writable_runtime_dir(performance_dir)
        self.performance_dir = Path(performance_dir)
        self.performance_dir.mkdir(parents=True, exist_ok=True)

    def record_performance(self, performance: ModelPerformance) -> None:
        """
        Record model performance metrics

        Args:
            performance: Performance metrics to record
        """
        performance_file = self.performance_dir / f"{performance.model_id}_{performance.model_version}.json"
        performance_dict = {
            'model_id': performance.model_id,
            'model_version': performance.model_version,
            'evaluation_period': performance.evaluation_period,
            'forecast_horizon': performance.forecast_horizon,
            'observation_count': performance.observation_count,
            'metrics': performance.metrics,
            'evaluation_timestamp': performance.evaluation_timestamp
        }

        with open(performance_file, 'w') as f:
            json.dump(performance_dict, f, indent=2)

    def get_performance_history(self, model_id: str, model_version: str) -> List[ModelPerformance]:
        """
        Get performance history for a specific model version

        Args:
            model_id: Model identifier
            model_version: Model version

        Returns:
            List of performance records
        """
        performances = []
        for perf_file in self.performance_dir.glob(f"{model_id}_{model_version}*.json"):
            try:
                with open(perf_file, 'r') as f:
                    perf_dict = json.load(f)
                    performance = ModelPerformance(
                        model_id=perf_dict['model_id'],
                        model_version=perf_dict['model_version'],
                        evaluation_period=perf_dict['evaluation_period'],
                        forecast_horizon=perf_dict['forecast_horizon'],
                        observation_count=perf_dict['observation_count'],
                        metrics=perf_dict['metrics'],
                        evaluation_timestamp=perf_dict['evaluation_timestamp']
                    )
                    performances.append(performance)
            except Exception as e:
                print(f"Error loading performance history {perf_file}: {e}")
                continue
        return performances

    def compare_performance(self, model_id: str, model_versions: List[str]) -> Dict[str, Any]:
        """
        Compare performance between different model versions

        Args:
            model_id: Model identifier
            model_versions: List of versions to compare

        Returns:
            Dictionary with comparison results
        """
        comparison = {}
        for version in model_versions:
            performances = self.get_performance_history(model_id, version)
            if performances:
                # Aggregate metrics across all evaluations
                avg_metrics = {}
                for perf in performances:
                    for metric_name, metric_value in perf.metrics.items():
                        if metric_name not in avg_metrics:
                            avg_metrics[metric_name] = []
                        avg_metrics[metric_name].append(metric_value)

                # Calculate averages
                comparison[version] = {
                    metric_name: sum(values)/len(values) if values else 0
                    for metric_name, values in avg_metrics.items()
                }

        return comparison

    def get_latest_performance(self, model_id: str, model_version: str) -> Optional[ModelPerformance]:
        """
        Get the most recent performance record for a model version

        Args:
            model_id: Model identifier
            model_version: Model version

        Returns:
            Latest performance record or None
        """
        performances = self.get_performance_history(model_id, model_version)
        if performances:
            # Sort by timestamp and return the latest
            performances.sort(key=lambda x: x.evaluation_timestamp, reverse=True)
            return performances[0]
        return None

    def track_forecast_vs_actual(self, model_id: str, model_version: str,
                               forecast_data: pd.DataFrame, actual_data: pd.DataFrame,
                               forecast_horizon: int = 1) -> Dict[str, float]:
        """
        Track forecast vs actual performance

        Args:
            model_id: Model identifier
            model_version: Model version
            forecast_data: DataFrame with forecast values
            actual_data: DataFrame with actual values
            forecast_horizon: Forecast horizon in days

        Returns:
            Dictionary with performance metrics
        """
        # Merge forecast and actual data
        merged = pd.merge(forecast_data, actual_data, left_index=True, right_index=True, how='inner')

        # Calculate metrics
        mae = abs(merged['forecast'] - merged['actual']).mean()
        rmse = (abs(merged['forecast'] - merged['actual']) ** 2).mean() ** 0.5

        # Handle MAPE and sMAPE calculation
        mask = (merged['actual'] != 0) & (merged['forecast'] != 0)
        if mask.any():
            mape = (abs((merged['actual'] - merged['forecast']) / merged['actual'])).mean() * 100
            smape = (abs(merged['actual'] - merged['forecast']) /
                    ((abs(merged['actual']) + abs(merged['forecast'])) / 2)).mean() * 100
        else:
            mape = 0
            smape = 0

        # Calculate mean bias error
        mbe = (merged['forecast'] - merged['actual']).mean()

        # Create performance record
        performance = ModelPerformance(
            model_id=model_id,
            model_version=model_version,
            evaluation_period=("unknown", "unknown"),  # Would be set based on actual data dates
            forecast_horizon=forecast_horizon,
            observation_count=len(merged),
            metrics={
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'smape': smape,
                'mbe': mbe
            },
            evaluation_timestamp=datetime.now().isoformat()
        )

        # Record performance
        self.record_performance(performance)

        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'smape': smape,
            'mbe': mbe
        }