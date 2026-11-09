"""
Generation analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.analytics.models import GenerationAnalysisResult
from src.analytics.data_access import GoldDataAccessor

class GenerationAnalyzer:
    """Analyzer for electricity generation data"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_generation(self,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> GenerationAnalysisResult:
        """
        Perform comprehensive generation analysis

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)

        Returns:
            GenerationAnalysisResult with comprehensive analysis
        """
        # Get generation data
        df = self.data_accessor.get_generation_data(start_date, end_date)

        if df.empty:
            raise ValueError("No generation data available for analysis")

        # Calculate basic metrics
        total_generation_mw = float(df['total_generation_mw'].sum())
        renewable_generation_mw = float(df['renewable_generation_mw'].sum())
        fossil_generation_mw = float(df['fossil_generation_mw'].sum())
        nuclear_generation_mw = float(df['nuclear_generation_mw'].sum())

        # Calculate generation mix percentages
        generation_mix = self._calculate_generation_mix(
            total_generation_mw, renewable_generation_mw, fossil_generation_mw, nuclear_generation_mw
        )

        # Get date range
        date_range = (df['timestamp'].min().strftime('%Y-%m-%d'),
                     df['timestamp'].max().strftime('%Y-%m-%d'))

        # Calculate daily trends
        daily_trends = self._calculate_daily_trends(df)

        # Calculate monthly trends
        monthly_trends = self._calculate_monthly_trends(df)

        # Calculate fuel type breakdown
        fuel_type_breakdown = {
            'renewable': renewable_generation_mw,
            'fossil': fossil_generation_mw,
            'nuclear': nuclear_generation_mw
        }

        return GenerationAnalysisResult(
            dataset_name='generation',
            date_range=date_range,
            total_generation_mw=total_generation_mw,
            renewable_generation_mw=renewable_generation_mw,
            fossil_generation_mw=fossil_generation_mw,
            nuclear_generation_mw=nuclear_generation_mw,
            generation_mix=generation_mix,
            daily_trends=daily_trends,
            monthly_trends=monthly_trends,
            fuel_type_breakdown=fuel_type_breakdown
        )

    def _calculate_generation_mix(self,
                                 total: float,
                                 renewable: float,
                                 fossil: float,
                                 nuclear: float) -> Dict[str, float]:
        """Calculate generation mix percentages"""
        if total == 0:
            return {'renewable': 0, 'fossil': 0, 'nuclear': 0}

        return {
            'renewable': float((renewable / total) * 100),
            'fossil': float((fossil / total) * 100),
            'nuclear': float((nuclear / total) * 100)
        }

    def _calculate_daily_trends(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate average daily generation trends"""
        df_copy = df.copy()
        df_copy['day_of_week'] = df_copy['timestamp'].dt.day_name()
        daily_avg = df_copy.groupby('day_of_week')['total_generation_mw'].mean().to_dict()
        # Ensure all days are present
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in weekdays:
            if day not in daily_avg:
                daily_avg[day] = 0.0
        return daily_avg

    def _calculate_monthly_trends(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate monthly generation trends"""
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month_name()
        monthly_avg = df_copy.groupby('month')['total_generation_mw'].mean().to_dict()
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