"""
Statistical analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.analytics.models import StatisticalAnalysisResult
from src.analytics.data_access import GoldDataAccessor
from loguru import logger

class StatisticalAnalyzer:
    """Analyzer for statistical analysis"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_statistics(self,
                          dataset_name: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> StatisticalAnalysisResult:
        """
        Perform comprehensive statistical analysis

        Args:
            dataset_name: Name of the dataset to analyze ('demand', 'generation', or 'weather')
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)

        Returns:
            StatisticalAnalysisResult with statistical analysis
        """
        # Get the requested dataset
        if dataset_name == 'demand':
            df = self.data_accessor.get_demand_data(start_date, end_date)
            if df.empty:
                raise ValueError("No demand data available for analysis")
            target_columns = ['demand_mw', 'demand_mwh']
        elif dataset_name == 'generation':
            df = self.data_accessor.get_generation_data(start_date, end_date)
            if df.empty:
                raise ValueError("No generation data available for analysis")
            target_columns = ['total_generation_mw', 'renewable_generation_mw', 'fossil_generation_mw', 'nuclear_generation_mw']
        elif dataset_name == 'weather':
            df = self.data_accessor.get_weather_data(start_date, end_date)
            if df.empty:
                raise ValueError("No weather data available for analysis")
            target_columns = ['temperature_celsius', 'humidity_percent', 'wind_speed_mps', 'precipitation_mm']
        else:
            raise ValueError(f"Unsupported dataset: {dataset_name}")

        # Calculate rolling averages
        rolling_averages = self._calculate_rolling_averages(df, target_columns)

        # Calculate percentage changes
        percentage_changes = self._calculate_percentage_changes(df, target_columns)

        # Calculate standard deviations
        standard_deviations = self._calculate_standard_deviations(df, target_columns)

        # Calculate interquartile ranges
        interquartile_ranges = self._calculate_interquartile_ranges(df, target_columns)

        # Calculate trends
        trends = self._calculate_trends(df, target_columns)

        # Identify outliers
        outliers = self._identify_outliers(df, target_columns)

        # Calculate distribution summary
        distribution_summary = self._calculate_distribution_summary(df, target_columns)

        # Get date range
        # Ensure timestamp is properly converted to datetime
        try:
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            date_range = (df['timestamp'].min().strftime('%Y-%m-%d'),
                          df['timestamp'].max().strftime('%Y-%m-%d'))
        except Exception as e:
            # Fallback in case of timestamp conversion issues
            logger.warning(f"Could not convert timestamps: {e}")
            date_range = ("1900-01-01", "1900-01-01")

        return StatisticalAnalysisResult(
            dataset_name=dataset_name,
            date_range=date_range,
            rolling_averages=rolling_averages,
            percentage_changes=percentage_changes,
            standard_deviations=standard_deviations,
            interquartile_ranges=interquartile_ranges,
            trends=trends,
            outliers=outliers,
            distribution_summary=distribution_summary
        )

    def _calculate_rolling_averages(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, List[float]]:
        """Calculate rolling averages (7-day windows)"""
        rolling_avgs = {}
        for col in columns:
            if col in df.columns:
                rolling_avgs[col] = df[col].rolling(window=7, min_periods=1).mean().tolist()
        return rolling_avgs

    def _calculate_percentage_changes(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, List[float]]:
        """Calculate percentage changes"""
        pct_changes = {}
        for col in columns:
            if col in df.columns:
                pct_changes[col] = df[col].pct_change().fillna(0).tolist()
        return pct_changes

    def _calculate_standard_deviations(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
        """Calculate standard deviations"""
        std_devs = {}
        for col in columns:
            if col in df.columns:
                std_devs[col] = float(df[col].std())
        return std_devs

    def _calculate_interquartile_ranges(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
        """Calculate interquartile ranges"""
        iqr_vals = {}
        for col in columns:
            if col in df.columns:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr_vals[col] = float(q3 - q1)
        return iqr_vals

    def _calculate_trends(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, str]:
        """Calculate trends (increasing, decreasing, stable)"""
        trends = {}
        for col in columns:
            if col in df.columns:
                # Simple linear trend analysis
                if len(df) >= 2:
                    # Use slope of linear regression
                    x = np.arange(len(df))
                    y = df[col].values
                    slope, _ = np.polyfit(x, y, 1)

                    if slope > 0.01:
                        trends[col] = "increasing"
                    elif slope < -0.01:
                        trends[col] = "decreasing"
                    else:
                        trends[col] = "stable"
                else:
                    trends[col] = "unknown"
        return trends

    def _identify_outliers(self, df: pd.DataFrame, columns: List[str]) -> List[Dict[str, Any]]:
        """Identify outliers using IQR method"""
        outliers = []
        for col in columns:
            if col in df.columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                # Find outliers
                outlier_indices = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index.tolist()

                for idx in outlier_indices:
                    outliers.append({
                        'column': col,
                        'index': int(idx),
                        'value': float(df.loc[idx, col]),
                        'timestamp': df.loc[idx, 'timestamp'].strftime('%Y-%m-%d')
                    })
        return outliers

    def _calculate_distribution_summary(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """Calculate distribution summary statistics"""
        summary = {}
        for col in columns:
            if col in df.columns:
                summary[col] = {
                    'count': int(df[col].count()),
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'std': float(df[col].std()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'q25': float(df[col].quantile(0.25)),
                    'q75': float(df[col].quantile(0.75))
                }
        return summary