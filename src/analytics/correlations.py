"""
Correlation analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.analytics.models import CorrelationAnalysisResult
from src.analytics.data_access import GoldDataAccessor
from loguru import logger

class CorrelationAnalyzer:
    """Analyzer for weather-demand correlation analysis"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_correlations(self,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> CorrelationAnalysisResult:
        """
        Perform comprehensive weather-demand correlation analysis

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)

        Returns:
            CorrelationAnalysisResult with correlation analysis
        """
        # Get all datasets
        datasets = self.data_accessor.get_all_datasets()

        demand_df = datasets['demand']
        weather_df = datasets['weather']

        if demand_df.empty or weather_df.empty:
            raise ValueError("Insufficient data for correlation analysis")

        # Align datasets by timestamp
        merged_df = self._align_datasets(demand_df, weather_df)

        if len(merged_df) < 2:
            raise ValueError("Insufficient aligned data for correlation analysis")

        # Calculate correlations
        pearson_corr = None
        spearman_corr = None

        try:
            # Pearson correlation (linear relationship)
            if len(merged_df) > 1:
                pearson_corr, _ = stats.pearsonr(merged_df['temperature_celsius'], merged_df['demand_mw'])

            # Spearman correlation (monotonic relationship)
            if len(merged_df) > 1:
                spearman_corr, _ = stats.spearmanr(merged_df['temperature_celsius'], merged_df['demand_mw'])
        except Exception as e:
            # Handle cases where correlation calculation fails
            print(f"Warning: Could not calculate correlations: {e}")

        # Determine correlation strength
        correlation_strength = self._determine_correlation_strength(pearson_corr)

        # Prepare key findings
        key_findings = self._generate_key_findings(pearson_corr, spearman_corr, len(merged_df))

        # Get date range
        # Ensure timestamp is properly converted to datetime
        try:
            if not pd.api.types.is_datetime64_any_dtype(merged_df['timestamp']):
                merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])
            date_range = (merged_df['timestamp'].min().strftime('%Y-%m-%d'),
                          merged_df['timestamp'].max().strftime('%Y-%m-%d'))
        except Exception as e:
            # Fallback in case of timestamp conversion issues
            logger.warning(f"Could not convert timestamps: {e}")
            date_range = ("1900-01-01", "1900-01-01")

        return CorrelationAnalysisResult(
            dataset_names=['demand', 'weather'],
            date_range=date_range,
            pearson_correlation=pearson_corr,
            spearman_correlation=spearman_corr,
            sample_size=len(merged_df),
            correlation_strength=correlation_strength,
            key_findings=key_findings
        )

    def _align_datasets(self, demand_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
        """Align demand and weather datasets by timestamp"""
        # Merge on timestamp
        merged = pd.merge(demand_df, weather_df, on='timestamp', how='inner')
        return merged

    def _determine_correlation_strength(self, pearson_corr: Optional[float]) -> str:
        """Determine correlation strength based on Pearson correlation coefficient"""
        if pearson_corr is None:
            return "insufficient"

        corr_abs = abs(pearson_corr)
        if corr_abs >= 0.7:
            return "strong"
        elif corr_abs >= 0.3:
            return "moderate"
        elif corr_abs >= 0.1:
            return "weak"
        else:
            return "very_weak"

    def _generate_key_findings(self, pearson_corr: Optional[float],
                             spearman_corr: Optional[float],
                             sample_size: int) -> List[str]:
        """Generate key findings from correlation analysis"""
        findings = []

        if sample_size < 10:
            findings.append(f"Sample size ({sample_size}) is relatively small for reliable correlation analysis")

        if pearson_corr is not None:
            findings.append(f"Pearson correlation coefficient: {pearson_corr:.3f}")

        if spearman_corr is not None:
            findings.append(f"Spearman correlation coefficient: {spearman_corr:.3f}")

        if pearson_corr is not None and abs(pearson_corr) > 0.3:
            direction = "positive" if pearson_corr > 0 else "negative"
            findings.append(f"Detected {direction} correlation between temperature and demand")

        return findings