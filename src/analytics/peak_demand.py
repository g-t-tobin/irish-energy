"""
Peak demand analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.analytics.models import PeakDemandAnalysisResult
from src.analytics.data_access import GoldDataAccessor

class PeakDemandAnalyzer:
    """Analyzer for peak demand data"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_peak_demand(self,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> PeakDemandAnalysisResult:
        """
        Perform comprehensive peak demand analysis
        
        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            PeakDemandAnalysisResult with comprehensive peak demand analysis
        """
        # Get demand data
        df = self.data_accessor.get_demand_data(start_date, end_date)

        if df.empty:
            raise ValueError("No demand data available for peak analysis")

        # Calculate basic metrics
        highest_recorded_demand = float(df['demand_mw'].max())
        lowest_recorded_demand = float(df['demand_mw'].min())
        average_demand = float(df['demand_mw'].mean())
        median_demand = float(df['demand_mw'].median())
        
        # Get date range
        date_range = (df['timestamp'].min().strftime('%Y-%m-%d'),
                     df['timestamp'].max().strftime('%Y-%m-%d'))

        # Find highest recorded demand period
        highest_demand_period = self._find_highest_demand_period(df)
        
        # Find lowest recorded demand period
        lowest_demand_period = self._find_lowest_demand_period(df)
        
        # Calculate daily peak demand
        daily_peak_demands = self._calculate_daily_peak_demands(df)
        
        # Calculate weekly peak demand
        weekly_peak_demands = self._calculate_weekly_peak_demands(df)
        
        # Calculate monthly peak demand
        monthly_peak_demands = self._calculate_monthly_peak_demands(df)
        
        # Calculate peak timing analysis
        peak_timing_analysis = self._analyze_peak_timing(df)
        
        # Calculate demand variability metrics
        demand_variability = self._calculate_demand_variability(df)
        
        # Calculate historical comparisons
        historical_comparisons = self._calculate_historical_comparisons(df)
        
        return PeakDemandAnalysisResult(
            dataset_name="demand",
            date_range=date_range,
            highest_recorded_demand_mw=highest_recorded_demand,
            lowest_recorded_demand_mw=lowest_recorded_demand,
            average_demand_mw=average_demand,
            median_demand_mw=median_demand,
            highest_demand_period=highest_demand_period,
            lowest_demand_period=lowest_demand_period,
            daily_peak_demands=daily_peak_demands,
            weekly_peak_demands=weekly_peak_demands,
            monthly_peak_demands=monthly_peak_demands,
            peak_timing_analysis=peak_timing_analysis,
            demand_variability=demand_variability,
            historical_comparisons=historical_comparisons
        )

    def _find_highest_demand_period(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find the highest recorded demand period"""
        max_row = df.loc[df['demand_mw'].idxmax()]
        return {
            "date": max_row['timestamp'].strftime('%Y-%m-%d'),
            "time": max_row['timestamp'].strftime('%H:%M'),
            "demand_mw": float(max_row['demand_mw']),
            "demand_mwh": float(max_row['demand_mwh'])
        }

    def _find_lowest_demand_period(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find the lowest recorded demand period"""
        min_row = df.loc[df['demand_mw'].idxmin()]
        return {
            "date": min_row['timestamp'].strftime('%Y-%m-%d'),
            "time": min_row['timestamp'].strftime('%H:%M'),
            "demand_mw": float(min_row['demand_mw']),
            "demand_mwh": float(min_row['demand_mwh'])
        }

    def _calculate_daily_peak_demands(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate peak demand by day of week"""
        df_copy = df.copy()
        df_copy['day_of_week'] = df_copy['timestamp'].dt.day_name()
        daily_max = df_copy.groupby('day_of_week')['demand_mw'].max().to_dict()
        
        # Ensure all days are present
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in weekdays:
            if day not in daily_max:
                daily_max[day] = 0.0
        return daily_max

    def _calculate_weekly_peak_demands(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate peak demand by week of year"""
        df_copy = df.copy()
        df_copy['week_of_year'] = df_copy['timestamp'].dt.isocalendar().week
        weekly_max = df_copy.groupby('week_of_year')['demand_mw'].max().to_dict()
        return weekly_max

    def _calculate_monthly_peak_demands(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate peak demand by month"""
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month_name()
        monthly_max = df_copy.groupby('month')['demand_mw'].max().to_dict()
        
        # Order months chronologically
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        ordered_monthly = {}
        for month in month_order:
            if month in monthly_max:
                ordered_monthly[month] = monthly_max[month]
            else:
                ordered_monthly[month] = 0.0
        return ordered_monthly

    def _analyze_peak_timing(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze timing patterns of peak demand"""
        df_copy = df.copy()
        df_copy['hour'] = df_copy['timestamp'].dt.hour
        df_copy['day_of_week'] = df_copy['timestamp'].dt.day_name()
        
        # Hourly peak analysis
        hourly_peaks = df_copy.groupby('hour')['demand_mw'].max().to_dict()
        
        # Day of week peak analysis
        daily_peaks = df_copy.groupby('day_of_week')['demand_mw'].max().to_dict()
        
        # Most common peak hour
        most_common_peak_hour = df_copy['hour'].mode().iloc[0] if not df_copy['hour'].mode().empty else 0
        
        # Most common peak day
        most_common_peak_day = df_copy['day_of_week'].mode().iloc[0] if not df_copy['day_of_week'].mode().empty else "Unknown"
        
        return {
            "hourly_distribution": hourly_peaks,
            "daily_distribution": daily_peaks,
            "most_common_peak_hour": most_common_peak_hour,
            "most_common_peak_day": most_common_peak_day
        }

    def _calculate_demand_variability(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate demand variability metrics"""
        if len(df) < 2:
            return {
                "standard_deviation_mw": 0.0,
                "coefficient_of_variation": 0.0,
                "range_mw": 0.0,
                "interquartile_range_mw": 0.0
            }
            
        std_dev = float(df['demand_mw'].std())
        mean_demand = float(df['demand_mw'].mean())
        coefficient_of_variation = std_dev / mean_demand if mean_demand != 0 else 0.0
        data_range = float(df['demand_mw'].max() - df['demand_mw'].min())
        q1 = df['demand_mw'].quantile(0.25)
        q3 = df['demand_mw'].quantile(0.75)
        iqr = float(q3 - q1)
        
        return {
            "standard_deviation_mw": std_dev,
            "coefficient_of_variation": coefficient_of_variation,
            "range_mw": data_range,
            "interquartile_range_mw": iqr
        }

    def _calculate_historical_comparisons(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate historical comparisons"""
        # Simple comparison to average
        avg_demand = float(df['demand_mw'].mean())
        highest_demand = float(df['demand_mw'].max())
        
        # Calculate percentage above/below average
        percentage_above_average = ((highest_demand - avg_demand) / avg_demand) * 100 if avg_demand != 0 else 0
        
        # Find periods significantly above average (e.g., 20% above)
        significant_peaks = df[df['demand_mw'] > avg_demand * 1.2]
        
        return {
            "average_demand_mw": avg_demand,
            "highest_demand_mw": highest_demand,
            "percentage_above_average": percentage_above_average,
            "significant_peak_periods": len(significant_peaks),
            "significant_peak_dates": [
                row['timestamp'].strftime('%Y-%m-%d') 
                for _, row in significant_peaks.iterrows()
            ] if not significant_peaks.empty else []
        }