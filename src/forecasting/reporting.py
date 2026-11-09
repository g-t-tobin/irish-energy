"""
Reporting for forecasting results
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.forecasting.models import ForecastResult, ModelEvaluationResult

class ForecastingReporter:
    """Generate reports for forecasting results"""

    def __init__(self):
        pass

    def generate_forecast_report(self,
                                forecast: ForecastResult,
                                model_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a structured forecast report

        Args:
            forecast: Forecast result
            model_info: Additional model information

        Returns:
            Dictionary with forecast report
        """
        report = {
            'forecast_timestamp': forecast.forecast_timestamp,
            'predicted_demand_mw': forecast.predicted_demand_mw,
            'forecast_horizon_days': forecast.forecast_horizon_days,
            'model_identifier': forecast.model_identifier,
            'model_version': forecast.model_version,
            'generation_timestamp': forecast.generation_timestamp,
            'metadata': forecast.metadata,
            'report_generated_at': datetime.now().isoformat()
        }

        if model_info:
            report['model_info'] = model_info

        return report

    def generate_evaluation_report(self,
                                  evaluation_results: Dict[str, ModelEvaluationResult],
                                  baseline_comparison: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a structured evaluation report

        Args:
            evaluation_results: Dictionary of model evaluation results
            baseline_comparison: Comparison against baseline models

        Returns:
            Dictionary with evaluation report
        """
        report = {
            'evaluation_timestamp': datetime.now().isoformat(),
            'models_evaluated': len(evaluation_results),
            'model_results': {},
            'baseline_comparison': baseline_comparison or {},
            'summary_statistics': {}
        }

        # Process each model result
        for model_name, result in evaluation_results.items():
            report['model_results'][model_name] = {
                'model_identifier': result.model_identifier,
                'model_version': result.model_version,
                'forecast_horizon_days': result.forecast_horizon_days,
                'training_period': result.training_period,
                'evaluation_period': result.evaluation_period,
                'observation_count': result.observation_count,
                'metrics': result.metrics,
                'limitations': result.limitations,
                'seasonal_performance': result.seasonal_performance
            }

        # Calculate summary statistics
        if evaluation_results:
            all_metrics = [result.metrics for result in evaluation_results.values()]
            summary_stats = {}
            for metric_name in all_metrics[0].keys():
                values = [metrics[metric_name] for metrics in all_metrics]
                summary_stats[metric_name] = {
                    'mean': np.mean(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'std': np.std(values)
                }
            report['summary_statistics'] = summary_stats

        return report

    def generate_comparison_report(self,
                                  model_results: Dict[str, ModelEvaluationResult],
                                  baseline_results: Dict[str, ModelEvaluationResult]) -> Dict[str, Any]:
        """
        Generate a comparison report between models and baselines

        Args:
            model_results: Results from ML models
            baseline_results: Results from baseline models

        Returns:
            Dictionary with comparison report
        """
        report = {
            'comparison_timestamp': datetime.now().isoformat(),
            'models': {},
            'baselines': {},
            'model_comparison': {},
            'recommendation': ''
        }

        # Process ML models
        for model_name, result in model_results.items():
            report['models'][model_name] = {
                'metrics': result.metrics,
                'forecast_horizon': result.forecast_horizon_days
            }

        # Process baselines
        for baseline_name, result in baseline_results.items():
            report['baselines'][baseline_name] = {
                'metrics': result.metrics,
                'forecast_horizon': result.forecast_horizon_days
            }

        # Compare models against baselines
        if model_results and baseline_results:
            # Simple comparison by MAE
            best_model = None
            best_mae = float('inf')

            for model_name, model_result in model_results.items():
                if 'mae' in model_result.metrics:
                    mae = model_result.metrics['mae']
                    if mae < best_mae:
                        best_mae = mae
                        best_model = model_name

            # Find worst baseline
            worst_baseline = None
            worst_mae = 0
            for baseline_name, baseline_result in baseline_results.items():
                if 'mae' in baseline_result.metrics:
                    mae = baseline_result.metrics['mae']
                    if mae > worst_mae:
                        worst_mae = mae
                        worst_baseline = baseline_name

            # Generate recommendation
            if best_model and worst_baseline:
                if best_mae < worst_mae:
                    report['recommendation'] = f"Model {best_model} outperforms baseline {worst_baseline} by {worst_mae - best_mae:.2f} MAE"
                else:
                    report['recommendation'] = f"Baseline {worst_baseline} performs better than any ML model"
            else:
                report['recommendation'] = "Insufficient data for meaningful comparison"

        return report