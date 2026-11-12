"""
Demand analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from src.analytics.models import DemandAnalysisResult
from src.analytics.data_access import GoldDataAccessor
from loguru import logger

class DemandAnalyzer:
    """Analyzer for electricity demand data"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_demand(self,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> DemandAnalysisResult:
        """
        Perform comprehensive demand analysis

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)

        Returns:
            DemandAnalysisResult with comprehensive analysis
        """
        # Get demand data
        df = self.data_accessor.get_demand_data(start_date, end_date)

        if df.empty:
            raise ValueError("No demand data available for analysis")

        # Calculate basic metrics
        total_demand_mwh = float(df['demand_mwh'].sum())
        average_demand_mw = float(df['demand_mw'].mean())
        min_demand_mw = float(df['demand_mw'].min())
        max_demand_mw = float(df['demand_mw'].max())
        median_demand_mw = float(df['demand_mw'].median())

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

        # Find peak demand periods (top 5 highest demand days)
        peak_demand_periods = self._find_peak_periods(df)

        # Calculate daily profiles (average by day of week)
        daily_profiles = self._calculate_daily_profiles(df)

        # Calculate weekly patterns (average by week)
        weekly_patterns = self._calculate_weekly_patterns(df)

        # Calculate monthly patterns
        monthly_patterns = self._calculate_monthly_patterns(df)

        # Calculate seasonal patterns
        seasonal_patterns = self._calculate_seasonal_patterns(df)

        # Calculate growth rate (if more than one year)
        growth_rate = self._calculate_growth_rate(df)

        return DemandAnalysisResult(
            dataset_name='demand',
            date_range=date_range,
            total_demand_mwh=total_demand_mwh,
            average_demand_mw=average_demand_mw,
            min_demand_mw=min_demand_mw,
            max_demand_mw=max_demand_mw,
            median_demand_mw=median_demand_mw,
            peak_demand_periods=peak_demand_periods,
            daily_profiles=daily_profiles,
            weekly_patterns=weekly_patterns,
            monthly_patterns=monthly_patterns,
            seasonal_patterns=seasonal_patterns,
            growth_rate=growth_rate
        )

    def _find_peak_periods(self, df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
        """Find peak demand periods"""
        top_peaks = df.nlargest(top_n, 'demand_mw')
        return [
            {
                'date': row['timestamp'].strftime('%Y-%m-%d'),
                'demand_mw': float(row['demand_mw']),
                'demand_mwh': float(row['demand_mwh'])
            }
            for _, row in top_peaks.iterrows()
        ]

    def _calculate_daily_profiles(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate average demand by day of week"""
        df_copy = df.copy()
        df_copy['day_of_week'] = df_copy['timestamp'].dt.day_name()
        daily_avg = df_copy.groupby('day_of_week')['demand_mw'].mean().to_dict()
        # Ensure all days are present
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in weekdays:
            if day not in daily_avg:
                daily_avg[day] = 0.0
        return daily_avg

    def _calculate_weekly_patterns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate weekly demand patterns"""
        df_copy = df.copy()
        df_copy['week_of_year'] = df_copy['timestamp'].dt.isocalendar().week
        weekly_avg = df_copy.groupby('week_of_year')['demand_mw'].mean().to_dict()
        return weekly_avg

    def _calculate_monthly_patterns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate monthly demand patterns"""
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month_name()
        monthly_avg = df_copy.groupby('month')['demand_mw'].mean().to_dict()
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

    def _calculate_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate seasonal demand patterns"""
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
        seasonal_avg = df_copy.groupby('season')['demand_mw'].mean().to_dict()
        return seasonal_avg

    def _calculate_growth_rate(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate annual growth rate (simplified for single year)"""
        if len(df) < 2:
            return None

        # For a single year, growth rate is not meaningful
        # Return None to indicate this limitation
        return None