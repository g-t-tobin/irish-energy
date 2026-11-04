from typing import List, Dict, Any
import boto3
import pandas as pd
from io import BytesIO
from loguru import logger
from datetime import datetime
import os
import sys

# Import configuration
sys.path.insert(0, 'src')
from common.config import Config

class S3GoldDataRetriever:
    def __init__(self):
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'eu-west-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', Config.GOLD_BUCKET)
    
    def _read_parquet_from_s3(self, key: str) -> pd.DataFrame:
        """Read parquet file from S3 into pandas DataFrame"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            buffer = BytesIO(response['Body'].read())
            df = pd.read_parquet(buffer)
            return df
        except Exception as e:
            logger.error(f"Error reading {key} from S3: {e}")
            raise
    
    def get_demand_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Retrieve demand data from Gold layer"""
        try:
            # Construct the S3 key based on date range
            if start_date and end_date:
                # Format dates for S3 key (assuming YYYY-MM-DD format)
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                # For simplicity, we'll just get the latest available data
                # In a real implementation, you'd filter by date range
                key = "demand/demand_data.parquet"
            else:
                key = "demand/demand_data.parquet"
            
            df = self._read_parquet_from_s3(key)
            
            # Convert to list of dictionaries for API response
            # Ensure we're returning the right fields according to the frontend model
            records = df.to_dict('records')
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving demand data: {e}")
            # Return empty list or raise exception based on requirements
            return []
    
    def get_weather_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Retrieve weather data from Gold layer"""
        try:
            # Construct the S3 key based on date range
            if start_date and end_date:
                # For simplicity, we'll just get the latest available data
                key = "weather/weather_data.parquet"
            else:
                key = "weather/weather_data.parquet"
            
            df = self._read_parquet_from_s3(key)
            
            # Convert to list of dictionaries for API response
            records = df.to_dict('records')
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving weather data: {e}")
            return []
    
    def get_generation_data(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Retrieve generation data from Gold layer"""
        try:
            # Construct the S3 key based on date range
            if start_date and end_date:
                # For simplicity, we'll just get the latest available data
                key = "generation/generation_data.parquet"
            else:
                key = "generation/generation_data.parquet"
            
            df = self._read_parquet_from_s3(key)
            
            # Convert to list of dictionaries for API response
            records = df.to_dict('records')
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving generation data: {e}")
            return []
    
    def get_quality_metrics(self) -> List[Dict[str, Any]]:
        """Retrieve data quality metrics from Gold layer"""
        try:
            key = "quality/data_quality_metrics.parquet"
            df = self._read_parquet_from_s3(key)
            
            # Convert to list of dictionaries for API response
            records = df.to_dict('records')
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving quality metrics: {e}")
            return []
    
    def get_summary_data(self) -> Dict[str, Any]:
        """Retrieve summary data about the Gold layer"""
        try:
            key = "summary/summary_data.parquet"
            df = self._read_parquet_from_s3(key)
            
            # Convert to dictionary for API response
            record = df.to_dict('records')[0] if len(df) > 0 else {}
            return record
            
        except Exception as e:
            logger.error(f"Error retrieving summary data: {e}")
            return {}