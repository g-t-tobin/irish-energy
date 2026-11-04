"""
Gold layer processor for analytical datasets
"""

import pandas as pd
import boto3
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional
from loguru import logger
from src.common.config import Config


class GoldLayerProcessor:
    """
    Handles Gold layer operations for analytical datasets
    """

    def __init__(self):
        self.config = Config()
        self.s3_client = boto3.client('s3')

    def transform_to_gold(self, data_type: str, silver_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Transform Silver layer data to Gold layer format
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            silver_df: DataFrame from Silver layer
            
        Returns:
            Pandas DataFrame or None if error
        """
        try:
            if data_type == 'demand':
                return self._transform_demand_to_gold(silver_df)
            elif data_type == 'weather':
                return self._transform_weather_to_gold(silver_df)
            elif data_type == 'generation':
                return self._transform_generation_to_gold(silver_df)
            else:
                logger.error(f"Unknown data type: {data_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error transforming {data_type} to Gold layer: {str(e)}")
            return None

    def _transform_demand_to_gold(self, silver_df: pd.DataFrame) -> pd.DataFrame:
        """Transform demand data to Gold layer format"""
        # Group by date and calculate summary statistics
        grouped = silver_df.groupby('date').agg({
            'value': ['sum', 'mean', 'min', 'max']
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ['date', 'total_demand', 'avg_demand', 'min_demand', 'max_demand']
        
        return grouped

    def _transform_weather_to_gold(self, silver_df: pd.DataFrame) -> pd.DataFrame:
        """Transform weather data to Gold layer format"""
        # Group by date and calculate summary statistics
        if not silver_df.empty:
            # Convert timestamp to date for grouping
            silver_df['date'] = silver_df['timestamp'].dt.date
            grouped = silver_df.groupby('date').agg({
                'temperature': ['mean', 'min', 'max'],
                'humidity': ['mean']
            }).reset_index()
            
            # Flatten column names
            grouped.columns = ['date', 'avg_temperature', 'min_temperature', 'max_temperature', 'avg_humidity']
            
            return grouped
        else:
            return pd.DataFrame()

    def _transform_generation_to_gold(self, silver_df: pd.DataFrame) -> pd.DataFrame:
        """Transform generation data to Gold layer format"""
        # Group by date and fuel type, calculate summary statistics
        if not silver_df.empty:
            grouped = silver_df.groupby(['date', 'fuel_type']).agg({
                'value': ['sum', 'mean']
            }).reset_index()
            
            # Flatten column names
            grouped.columns = ['date', 'fuel_type', 'total_generation', 'avg_generation']
            
            return grouped
        else:
            return pd.DataFrame()

    def store_gold_data(self, key: str, df: pd.DataFrame) -> bool:
        """
        Store analytical data in Gold layer as Parquet
        
        Args:
            key: S3 object key
            df: Pandas DataFrame to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert DataFrame to Parquet format
            table = pa.Table.from_pandas(df)
            
            # Write to buffer
            buffer = BytesIO()
            pq.write_table(table, buffer)
            buffer.seek(0)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.config.GOLD_BUCKET,
                Key=key,
                Body=buffer.getvalue(),
                ContentType='application/octet-stream'
            )
            
            logger.info(f"Stored Gold data at {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing Gold data: {str(e)}")
            return False

    def retrieve_gold_data(self, key: str) -> Optional[pd.DataFrame]:
        """
        Retrieve analytical data from Gold layer
        
        Args:
            key: S3 object key
            
        Returns:
            Pandas DataFrame or None if not found
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.GOLD_BUCKET,
                Key=key
            )
            
            # Read Parquet from buffer
            buffer = BytesIO(response['Body'].read())
            table = pq.read_table(buffer)
            df = table.to_pandas()
            
            logger.info(f"Retrieved Gold data from {key}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving Gold data from {key}: {str(e)}")
            return None

    def list_gold_files(self, prefix: str = "") -> list:
        """
        List all files in Gold layer
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file keys
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.config.GOLD_BUCKET,
                Prefix=prefix
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
                        
            return files
            
        except Exception as e:
            logger.error(f"Error listing Gold files: {str(e)}")
            return []