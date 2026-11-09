"""
Renewable energy analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.analytics.models import RenewableAnalysisResult
from src.analytics.data_access import GoldDataAccessor

class RenewableAnalyzer:
    """Analyzer for renewable energy data"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_renewables(self,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> RenewableAnalysisResult:
        """
        Perform comprehensive renewable energy analysis

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)

        Returns:
            RenewableAnalysisResult with comprehensive analysis
        """
        # Get generation data
        df = self.data_accessor.get_generation_data(start_date, end_date)

        if df.empty:
            raise ValueError("No generation data available for renewable analysis")

        # Calculate basic metrics
        renewable_generation_mw = float(df['renewable_generation_mw'].sum())
        total_generation_mw = float(df['total_generation_mw'].sum())

        # Calculate renewable share percentage
        renewable_share_percentage = 0.0
        if total_generation_mw > 0:
            renewable_share_percentage = float((renewable_generation_mw / total_generation_mw) * 100)

        # Get date range
        date_range = (df['timestamp'].min().strftime('%Y-%m-%d'),
                     df['timestamp'].max().strftime('%Y-%m-%d'))

        # Calculate renewable trends
        renewable_trends = self._calculate_renewable_trends(df)

        # Calculate seasonal contribution
        seasonal_contribution = self._calculate_seasonal_contribution(df)

        # Find peak renewable periods
        peak_renewable_periods = self._find_peak_renewable_periods(df)

        return RenewableAnalysisResult(
            dataset_name='generation',
            date_range=date_range,
            renewable_generation_mw=renewable_generation_mw,
            total_generation_mw=total_generation_mw,
            renewable_share_percentage=renewable_share_percentage,
            renewable_trends=renewable_trends,
            seasonal_contribution=seasonal_contribution,
            peak_renewable_periods=peak_renewable_periods
        )

    def _calculate_renewable_trends(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate renewable generation trends"""
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month_name()
        monthly_avg = df_copy.groupby('month')['renewable_generation_mw'].mean().to_dict()
        # Order months chronologically
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        ordered_monthly = {}
        for month in month_order:
            if month in monthly_avg:
                ordered_monthly[month] = monthly_avg[month]
            else:
                ordered_monthly[month] = 0.0
        return ordered_monthly

    def _calculate_seasonal_contribution(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate seasonal renewable contribution"""
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month

        # Define seasons
        def get_season(month):
            if month in [12, 1, 2]:
                return 'Winter'
            elif month in [3, 4, 5]:
                return 'Spring'
            elif month in [6, 7, 8]:
                return 'Summer'
            else:
                return 'Fall'

        df_copy['season'] = df_copy['month'].apply(get_season)
        seasonal_avg = df_copy.groupby('season')['renewable_generation_mw'].mean().to_dict()
        return seasonal_avg

    def _find_peak_renewable_periods(self, df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
        """Find peak renewable generation periods"""
        top_renewable = df.nlargest(top_n, 'renewable_generation_mw')
        return [
            {
                'date': row['timestamp'].strftime('%Y-%m-%d'),
                'renewable_generation_mw': float(row['renewable_generation_mw']),
                'total_generation_mw': float(row['total_generation_mw'])
            }
            for _, row in top_renewable.iterrows()
        ]