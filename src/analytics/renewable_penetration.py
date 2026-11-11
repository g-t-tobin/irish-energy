"""
Renewable energy penetration analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.analytics.models import RenewableAnalysisResult
from src.analytics.data_access import GoldDataAccessor

class RenewablePenetrationAnalyzer:
    """Analyzer for renewable energy penetration data"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_renewable_penetration(self,
                                     start_date: Optional[str] = None,
                                     end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive renewable energy penetration analysis
        
        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            Dictionary with comprehensive renewable penetration analysis
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

        # Calculate renewable penetration by source (where available)
        renewable_by_source = self._calculate_renewable_by_source(df)

        # Calculate penetration over time
        penetration_over_time = self._calculate_penetration_over_time(df)

        return {
            "dataset_name": "generation",
            "date_range": date_range,
            "renewable_generation_mw": renewable_generation_mw,
            "total_generation_mw": total_generation_mw,
            "renewable_share_percentage": renewable_share_percentage,
            "renewable_trends": renewable_trends,
            "seasonal_contribution": seasonal_contribution,
            "peak_renewable_periods": peak_renewable_periods,
            "renewable_by_source": renewable_by_source,
            "penetration_over_time": penetration_over_time,
            "calculation_timestamp": datetime.now().isoformat()
        }

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

    def _calculate_renewable_by_source(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate renewable generation by source (where available)"""
        # This assumes the dataset has separate columns for different renewable sources
        # We'll check what's available and calculate accordingly
        renewable_by_source = {}
        
        # Check for wind generation data
        if 'wind_generation_mw' in df.columns:
            renewable_by_source['wind'] = float(df['wind_generation_mw'].sum())
        
        # Check for solar generation data  
        if 'solar_generation_mw' in df.columns:
            renewable_by_source['solar'] = float(df['solar_generation_mw'].sum())
            
        # Check for hydro generation data
        if 'hydro_generation_mw' in df.columns:
            renewable_by_source['hydro'] = float(df['hydro_generation_mw'].sum())
            
        # Check for other renewable data
        if 'other_renewable_generation_mw' in df.columns:
            renewable_by_source['other'] = float(df['other_renewable_generation_mw'].sum())
            
        return renewable_by_source

    def _calculate_penetration_over_time(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate renewable penetration over time"""
        penetration_list = []
        
        # Group by date and calculate penetration
        df_copy = df.copy()
        df_copy['date'] = df_copy['timestamp'].dt.date
        
        for date, group in df_copy.groupby('date'):
            total_gen = group['total_generation_mw'].sum()
            renewable_gen = group['renewable_generation_mw'].sum()
            
            penetration_percentage = 0.0
            if total_gen > 0:
                penetration_percentage = float((renewable_gen / total_gen) * 100)
            
            penetration_entry = {
                'date': str(date),
                'total_generation_mw': float(total_gen),
                'renewable_generation_mw': float(renewable_gen),
                'penetration_percentage': penetration_percentage
            }
            penetration_list.append(penetration_entry)
        
        return penetration_list