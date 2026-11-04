"""
Silver layer processor for validated Parquet data storage
"""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
from datetime import datetime
from io import BytesIO
from typing import Dict, Any, Optional
from loguru import logger
from src.common.config import Config


class SilverLayerProcessor:
    """
    Handles Silver layer operations for validated Parquet data
    """

    def __init__(self):
        self.config = Config()
        self.s3_client = boto3.client('s3')

    def transform_to_silver(self, data_type: str, raw_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Transform raw data to Silver layer format
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            raw_data: Raw data from Bronze layer
            
        Returns:
            Pandas DataFrame or None if error
        """
        try:
            if data_type == 'demand':
                return self._transform_demand_to_silver(raw_data)
            elif data_type == 'weather':
                return self._transform_weather_to_silver(raw_data)
            elif data_type == 'generation':
                return self._transform_generation_to_silver(raw_data)
            else:
                logger.error(f"Unknown data type: {data_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error transforming {data_type} to Silver layer: {str(e)}")
            return None

    def _transform_demand_to_silver(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Transform demand data to Silver layer format"""
        records = []
        date_str = raw_data['date']
        
        for entry in raw_data['demand_values']:
            records.append({
                'date': date_str,
                'timestamp': pd.to_datetime(entry['timestamp']),
                'value': entry['value']
            })
            
        return pd.DataFrame(records)

    def _transform_weather_to_silver(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Transform weather data to Silver layer format"""
        records = []
        
        # For simplicity, we'll extract hourly data points
        if 'hourly' in raw_data and 'time' in raw_data['hourly']:
            timestamps = raw_data['hourly']['time']
            temperatures = raw_data['hourly']['temperature_2m']
            
            for i, timestamp in enumerate(timestamps):
                if i < len(temperatures):
                    records.append({
                        'latitude': raw_data['latitude'],
                        'longitude': raw_data['longitude'],
                        'timestamp': pd.to_datetime(timestamp),
                        'temperature': temperatures[i],
                        'humidity': 0  # Placeholder - would come from other fields
                    })
                    
        return pd.DataFrame(records)

    def _transform_generation_to_silver(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Transform generation data to Silver layer format"""
        records = []
        date_str = raw_data['date']
        
        for entry in raw_data['generation_values']:
            records.append({
                'date': date_str,
                'timestamp': pd.to_datetime(entry['timestamp']),
                'value': entry['value'],
                'fuel_type': entry['fuel_type']
            })
            
        return pd.DataFrame(records)

    def store_silver_data(self, key: str, df: pd.DataFrame) -> bool:
        """
        Store validated data in Silver layer as Parquet
        
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
                Bucket=self.config.SILVER_BUCKET,
                Key=key,
                Body=buffer.getvalue(),
                ContentType='application/octet-stream'
            )
            
            logger.info(f"Stored Silver data at {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing Silver data: {str(e)}")
            return False

    def retrieve_silver_data(self, key: str) -> Optional[pd.DataFrame]:
        """
        Retrieve validated data from Silver layer
        
        Args:
            key: S3 object key
            
        Returns:
            Pandas DataFrame or None if not found
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.SILVER_BUCKET,
                Key=key
            )
            
            # Read Parquet from buffer
            buffer = BytesIO(response['Body'].read())
            table = pq.read_table(buffer)
            df = table.to_pandas()
            
            logger.info(f"Retrieved Silver data from {key}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving Silver data from {key}: {str(e)}")
            return None

    def list_silver_files(self, prefix: str = "") -> list:
        """
        List all files in Silver layer
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file keys
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.config.SILVER_BUCKET,
                Prefix=prefix
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
                        
            return files
            
        except Exception as e:
            logger.error(f"Error listing Silver files: {str(e)}")
            return []