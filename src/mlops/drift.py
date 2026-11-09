"""
Drift detection for MLOps framework
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from src.common.runtime_paths import writable_runtime_dir
from scipy import stats
from src.mlops.models import DriftDetectionResult
from src.quality.data_quality import DataQualityChecker

class DriftDetector:
    """Detect data and prediction drift for forecasting models"""

    def __init__(self, drift_dir: str = "./model_drift"):
        drift_dir = writable_runtime_dir(drift_dir)
        self.drift_dir = Path(drift_dir)
        self.drift_dir.mkdir(parents=True, exist_ok=True)

    def detect_feature_drift(self,
                           current_data: pd.DataFrame,
                           reference_data: pd.DataFrame,
                           feature_names: List[str] = None) -> List[DriftDetectionResult]:
        """
        Detect drift in input features

        Args:
            current_data: Current data to analyze
            reference_data: Reference data for comparison
            feature_names: List of features to check (if None, check all)

        Returns:
            List of drift detection results
        """
        results = []

        if feature_names is None:
            feature_names = list(current_data.columns)

        for feature in feature_names:
            if feature not in current_data.columns or feature not in reference_data.columns:
                continue

            current_series = current_data[feature].dropna()
            reference_series = reference_data[feature].dropna()

            if len(current_series) == 0 or len(reference_series) == 0:
                continue

            # Calculate drift score using Kolmogorov-Smirnov test
            try:
                ks_statistic, p_value = stats.ks_2samp(current_series, reference_series)
                drift_detected = p_value < 0.05  # 5% significance level

                # Calculate additional statistics
                current_mean = current_series.mean()
                reference_mean = reference_series.mean()
                current_std = current_series.std()
                reference_std = reference_series.std()

                # Population Stability Index (PSI) calculation
                psi = self._calculate_psi(current_series, reference_series)

                result = DriftDetectionResult(
                    feature_name=feature,
                    drift_detected=drift_detected,
                    drift_score=ks_statistic,
                    drift_type="distribution_change",
                    previous_distribution={
                        'mean': reference_mean,
                        'std': reference_std,
                        'count': len(reference_series)
                    },
                    current_distribution={
                        'mean': current_mean,
                        'std': current_std,
                        'count': len(current_series)
                    },
                    timestamp=datetime.now().isoformat()
                )

                results.append(result)

            except Exception as e:
                print(f"Error detecting drift for feature {feature}: {e}")
                continue

        return results

    def _calculate_psi(self, current_series: pd.Series, reference_series: pd.Series) -> float:
        """
        Calculate Population Stability Index (PSI)

        Args:
            current_series: Current data series
            reference_series: Reference data series

        Returns:
            PSI value
        """
        # Create bins for both datasets
        combined_data = pd.concat([current_series, reference_series])
        min_val = combined_data.min()
        max_val = combined_data.max()

        # Create bins
        bins = np.linspace(min_val, max_val, 10)
        current_counts, _ = np.histogram(current_series, bins=bins)
        reference_counts, _ = np.histogram(reference_series, bins=bins)

        # Add small epsilon to avoid division by zero
        epsilon = 1e-10
        current_probs = (current_counts + epsilon) / len(current_series)
        reference_probs = (reference_counts + epsilon) / len(reference_series)

        # Calculate PSI
        psi = np.sum((current_probs - reference_probs) * np.log(current_probs / reference_probs))
        return psi

    def detect_prediction_drift(self,
                              current_predictions: pd.Series,
                              reference_predictions: pd.Series) -> DriftDetectionResult:
        """
        Detect drift in model predictions

        Args:
            current_predictions: Current predictions
            reference_predictions: Reference predictions

        Returns:
            Drift detection result
        """
        # Remove NaN values
        current_clean = current_predictions.dropna()
        reference_clean = reference_predictions.dropna()

        if len(current_clean) == 0 or len(reference_clean) == 0:
            return DriftDetectionResult(
                feature_name="prediction_drift",
                drift_detected=False,
                drift_score=0.0,
                drift_type="prediction_drift",
                previous_distribution={},
                current_distribution={},
                timestamp=datetime.now().isoformat()
            )

        # Statistical test for prediction drift
        try:
            ks_statistic, p_value = stats.ks_2samp(current_clean, reference_clean)
            drift_detected = p_value < 0.05

            # Additional drift metrics
            current_mean = current_clean.mean()
            reference_mean = reference_clean.mean()
            current_var = current_clean.var()
            reference_var = reference_clean.var()

            result = DriftDetectionResult(
                feature_name="prediction_drift",
                drift_detected=drift_detected,
                drift_score=ks_statistic,
                drift_type="prediction_drift",
                previous_distribution={
                    'mean': reference_mean,
                    'variance': reference_var,
                    'count': len(reference_clean)
                },
                current_distribution={
                    'mean': current_mean,
                    'variance': current_var,
                    'count': len(current_clean)
                },
                timestamp=datetime.now().isoformat()
            )

            return result

        except Exception as e:
            print(f"Error detecting prediction drift: {e}")
            return DriftDetectionResult(
                feature_name="prediction_drift",
                drift_detected=False,
                drift_score=0.0,
                drift_type="prediction_drift",
                previous_distribution={},
                current_distribution={},
                timestamp=datetime.now().isoformat()
            )

    def save_drift_result(self, result: DriftDetectionResult) -> None:
        """
        Save drift detection result to persistent storage

        Args:
            result: Drift detection result to save
        """
        result_file = self.drift_dir / f"{result.feature_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_dict = {
            'feature_name': result.feature_name,
            'drift_detected': result.drift_detected,
            'drift_score': result.drift_score,
            'drift_type': result.drift_type,
            'previous_distribution': result.previous_distribution,
            'current_distribution': result.current_distribution,
            'timestamp': result.timestamp
        }

        with open(result_file, 'w') as f:
            json.dump(result_dict, f, indent=2)

    def get_recent_drift_results(self, feature_name: str = None, limit: int = 10) -> List[DriftDetectionResult]:
        """
        Get recent drift detection results

        Args:
            feature_name: Specific feature to filter results (None for all)
            limit: Maximum number of results to return

        Returns:
            List of recent drift results
        """
        results = []
        pattern = f"*{feature_name}*" if feature_name else "*"

        for drift_file in self.drift_dir.glob(pattern):
            try:
                with open(drift_file, 'r') as f:
                    result_dict = json.load(f)
                    result = DriftDetectionResult(
                        feature_name=result_dict['feature_name'],
                        drift_detected=result_dict['drift_detected'],
                        drift_score=result_dict['drift_score'],
                        drift_type=result_dict['drift_type'],
                        previous_distribution=result_dict['previous_distribution'],
                        current_distribution=result_dict['current_distribution'],
                        timestamp=result_dict['timestamp']
                    )
                    results.append(result)
            except Exception as e:
                print(f"Error loading drift result {drift_file}: {e}")
                continue

        # Sort by timestamp descending and limit results
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]

    def detect_seasonal_drift(self,
                            data: pd.DataFrame,
                            feature_name: str,
                            season_length: int = 365) -> Dict[str, Any]:
        """
        Detect seasonal patterns and drift in data

        Args:
            data: Data to analyze
            feature_name: Feature to analyze
            season_length: Length of seasonal cycle (default 365 days)

        Returns:
            Dictionary with seasonal drift analysis
        """
        if feature_name not in data.columns:
            return {}

        series = data[feature_name]
        seasonal_analysis = {}

        # Analyze seasonal patterns
        for i in range(season_length):
            if i < len(series):
                seasonal_analysis[f"day_{i}"] = series.iloc[i]

        return seasonal_analysis