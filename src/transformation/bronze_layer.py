"""
Bronze layer processor for raw JSON data storage
"""

import json
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
from src.common.config import Config


class BronzeLayerProcessor:
    """
    Handles Bronze layer operations for raw data storage
    """

    def __init__(self, s3_client=None):
        self.config = Config()
        self.s3_client = s3_client or boto3.client('s3')

    def store_bronze_data(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Store raw data in Bronze layer
        
        Args:
            key: S3 object key
            data: Raw data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert data to JSON string
            json_data = json.dumps(data, indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.config.BRONZE_BUCKET,
                Key=key,
                Body=json_data,
                ContentType='application/json'
            )
            
            logger.info(f"Stored Bronze data at {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing Bronze data: {str(e)}")
            return False

    def retrieve_bronze_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve raw data from Bronze layer
        
        Args:
            key: S3 object key
            
        Returns:
            Dict with raw data or None if not found
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.BRONZE_BUCKET,
                Key=key
            )
            
            data = json.loads(response['Body'].read())
            logger.info(f"Retrieved Bronze data from {key}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving Bronze data from {key}: {str(e)}")
            return None

    def list_bronze_files(self, prefix: str = "") -> list:
        """
        List all files in Bronze layer
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file keys
        """
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.config.BRONZE_BUCKET,
                Prefix=prefix
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
                        
            return files
            
        except Exception as e:
            logger.error(f"Error listing Bronze files: {str(e)}")
            return []

    def list_timestamped_ingestion_objects(self, data_type: str, date_str: str, prefix: str = None) -> list:
        """
        List timestamped ingestion objects for a specific date
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            prefix: Optional prefix to filter files
            
        Returns:
            List of object metadata dictionaries with Key and LastModified
        """
        try:
            # Construct the prefix for timestamped ingestion objects
            if prefix is None:
                prefix = f"{data_type}/"
                if date_str:
                    prefix += f"{date_str}/"
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.config.BRONZE_BUCKET,
                Prefix=prefix
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Filter for timestamped files (those with timestamp in filename)
                        key = obj['Key']
                        if '_raw.json' in key or '.json' in key:
                            files.append({
                                'Key': key,
                                'LastModified': obj['LastModified']
                            })
                            
            return files
            
        except Exception as e:
            logger.error(f"Error listing timestamped ingestion objects: {str(e)}")
            raise  # Propagate AWS errors instead of returning empty list