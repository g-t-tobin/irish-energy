"""
Data access utilities for analytics package
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.services.data_service import S3GoldDataRetriever
from src.common.config import Config

class GoldDataAccessor:
    """Utility class for accessing Gold layer data for analytics"""

    def __init__(self, data_retriever: Optional[Any] = None):
        """Initialize with optional data retriever"""
        # If no retriever provided, initialize default S3GoldDataRetriever
        if data_retriever is None:
            from src.services.data_service import S3GoldDataRetriever
            from src.common.config import Config
            self.data_retriever = S3GoldDataRetriever(Config())
        else:
            self.data_retriever = data_retriever

    def get_demand_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get demand data from Gold layer"""
        try:
            data = self.data_retriever.get_demand_data(start_date, end_date)
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)
            return df
        except Exception as e:
            raise Exception(f"Error retrieving demand data: {str(e)}")

    def get_generation_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get generation data from Gold layer"""
        try:
            data = self.data_retriever.get_generation_data(start_date, end_date)
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)
            return df
        except Exception as e:
            raise Exception(f"Error retrieving generation data: {str(e)}")

    def get_weather_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get weather data from Gold layer"""
        try:
            data = self.data_retriever.get_weather_data(start_date, end_date)
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)
            return df
        except Exception as e:
            raise Exception(f"Error retrieving weather data: {str(e)}")

    def get_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """Get all datasets for comprehensive analysis"""
        datasets = {}
        datasets['demand'] = self.get_demand_data()
        datasets['generation'] = self.get_generation_data()
        datasets['weather'] = self.get_weather_data()
        return datasets