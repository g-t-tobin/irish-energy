"""
Weather analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from src.analytics.models import WeatherAnalysisResult
from src.analytics.data_access import GoldDataAccessor

class WeatherAnalyzer:
    """Analyzer for weather data"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_weather(self,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> WeatherAnalysisResult:
        """
        Perform comprehensive weather analysis

        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)

        Returns:
            WeatherAnalysisResult with comprehensive analysis
        """
        # Get weather data
        df = self.data_accessor.get_weather_data(start_date, end_date)

        if df.empty:
            raise ValueError("No weather data available for analysis")

        # Calculate basic metrics
        avg_temperature_celsius = float(df['temperature_celsius'].mean())
        avg_humidity_percent = float(df['humidity_percent'].mean())
        avg_wind_speed_mps = float(df['wind_speed_mps'].mean())
        avg_precipitation_mm = float(df['precipitation_mm'].mean())

        # Get date range
        date_range = (df['timestamp'].min().strftime('%Y-%m-%d'),
                     df['timestamp'].max().strftime('%Y-%m-%d'))

        # Calculate temperature trends
        temperature_trends = self._calculate_temperature_trends(df)

        # Calculate precipitation trends
        precipitation_trends = self._calculate_precipitation_trends(df)

        # Calculate weather patterns
        weather_patterns = self._calculate_weather_patterns(df)

        # Calculate seasonal weather patterns
        seasonal_weather = self._calculate_seasonal_weather(df)

        return WeatherAnalysisResult(
            dataset_name='weather',
            date_range=date_range,
            avg_temperature_celsius=avg_temperature_celsius,
            avg_humidity_percent=avg_humidity_percent,
            avg_wind_speed_mps=avg_wind_speed_mps,
            avg_precipitation_mm=avg_precipitation_mm,
            temperature_trends=temperature_trends,
            precipitation_trends=precipitation_trends,
            weather_patterns=weather_patterns,
            seasonal_weather=seasonal_weather
        )

    def _calculate_temperature_trends(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate temperature trends by month"""
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month_name()
        monthly_avg = df_copy.groupby('month')['temperature_celsius'].mean().to_dict()
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

    def _calculate_precipitation_trends(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate precipitation trends by month"""
        df_copy = df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month_name()
        monthly_avg = df_copy.groupby('month')['precipitation_mm'].mean().to_dict()
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

    def _calculate_weather_patterns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate basic weather patterns"""
        return {
            'avg_temperature': float(df['temperature_celsius'].mean()),
            'avg_humidity': float(df['humidity_percent'].mean()),
            'avg_wind_speed': float(df['wind_speed_mps'].mean()),
            'avg_precipitation': float(df['precipitation_mm'].mean()),
            'max_temperature': float(df['temperature_celsius'].max()),
            'min_temperature': float(df['temperature_celsius'].min()),
            'max_precipitation': float(df['precipitation_mm'].max())
        }

    def _calculate_seasonal_weather(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate seasonal weather patterns"""
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
        seasonal_avg = df_copy.groupby('season')['temperature_celsius'].mean().to_dict()
        return seasonal_avg