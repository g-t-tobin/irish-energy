"""
Data access utilities for forecasting package
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from services.data_service import S3GoldDataRetriever
from src.common.config import Config
from src.analytics.data_access import GoldDataAccessor

class ForecastingDataAccessor:
    """Utility class for accessing Gold layer data for forecasting"""

    def __init__(self, data_accessor: Optional[GoldDataAccessor] = None):
        """Initialize with optional data accessor"""
        self.data_accessor = data_accessor or GoldDataAccessor()

    def get_demand_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get demand data from Gold layer"""
        try:
            data = self.data_accessor.get_demand_data(start_date, end_date)
            if not data.empty:
                data = data.sort_values('timestamp').reset_index(drop=True)
            return data
        except Exception as e:
            raise Exception(f"Error retrieving demand data: {str(e)}")

    def get_weather_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get weather data from Gold layer"""
        try:
            data = self.data_accessor.get_weather_data(start_date, end_date)
            if not data.empty:
                data = data.sort_values('timestamp').reset_index(drop=True)
            return data
        except Exception as e:
            raise Exception(f"Error retrieving weather data: {str(e)}")

    def get_aligned_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get aligned demand and weather data"""
        try:
            demand_df = self.get_demand_data(start_date, end_date)
            weather_df = self.get_weather_data(start_date, end_date)

            if demand_df.empty or weather_df.empty:
                return pd.DataFrame()

            # Merge on timestamp
            merged_df = pd.merge(demand_df, weather_df, on='timestamp', how='inner')
            return merged_df.sort_values('timestamp').reset_index(drop=True)
        except Exception as e:
            raise Exception(f"Error aligning data: {str(e)}")