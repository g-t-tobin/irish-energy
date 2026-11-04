"""
Main data transformation pipeline for Bronze/Silver/Gold layers
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pyarrow as pa
import pyarrow.parquet as pq
from loguru import logger
import boto3
from io import BytesIO

from src.common.config import Config
from src.transformation.quality_checks import QualityChecker
from src.transformation.bronze_layer import BronzeLayerProcessor
from src.transformation.silver_layer import SilverLayerProcessor
from src.transformation.gold_layer import GoldLayerProcessor


class DataTransformer:
    """
    Main data transformation orchestrator for Bronze/Silver/Gold layers
    """

    def __init__(self):
        self.config = Config()
        self.quality_checker = QualityChecker()
        self.bronze_processor = BronzeLayerProcessor()
        self.silver_processor = SilverLayerProcessor()
        self.gold_processor = GoldLayerProcessor()
        self.s3_client = boto3.client('s3')

    def process_data_pipeline(self, data_type: str, date_str: str, raw_data: Dict[str, Any]) -> bool:
        """
        Complete data processing pipeline from Bronze to Gold layers
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            raw_data: Raw data from ingestion
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Starting data processing pipeline for {data_type} on {date_str}")
        
        try:
            # Step 1: Process Bronze layer
            bronze_success = self.process_bronze_layer(data_type, date_str, raw_data)
            if not bronze_success:
                logger.error(f"Failed to process Bronze layer for {data_type}")
                return False
                
            # Step 2: Process Silver layer
            silver_success = self.process_silver_layer(data_type, date_str)
            if not silver_success:
                logger.error(f"Failed to process Silver layer for {data_type}")
                return False
                
            # Step 3: Process Gold layer
            gold_success = self.process_gold_layer(data_type, date_str)
            if not gold_success:
                logger.error(f"Failed to process Gold layer for {data_type}")
                return False
                
            logger.info(f"Successfully completed data processing pipeline for {data_type} on {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error in data processing pipeline: {str(e)}")
            return False

    def validate_bronze_data(self, data: Dict[str, Any], data_type: str) -> bool:
        """
        Validate data at Bronze layer
        
        Args:
            data: Raw data to validate
            data_type: Type of data ('demand', 'weather', 'generation')
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if data_type == 'demand':
                # Check required fields for demand data
                required_fields = ['date', 'demand_values']
                for field in required_fields:
                    if field not in data:
                        logger.warning(f"Missing required field '{field}' in demand data")
                        return False
                
                # Validate demand values structure
                if not isinstance(data['demand_values'], list):
                    logger.warning("demand_values should be a list")
                    return False
                    
                # Validate each demand value entry
                for entry in data['demand_values']:
                    if not isinstance(entry, dict) or 'timestamp' not in entry or 'value' not in entry:
                        logger.warning("Invalid demand value entry structure")
                        return False
                        
            elif data_type == 'weather':
                # Check required fields for weather data
                required_fields = ['latitude', 'longitude', 'hourly', 'daily']
                for field in required_fields:
                    if field not in data:
                        logger.warning(f"Missing required field '{field}' in weather data")
                        return False
                        
            elif data_type == 'generation':
                # Check required fields for generation data
                required_fields = ['date', 'generation_values']
                for field in required_fields:
                    if field not in data:
                        logger.warning(f"Missing required field '{field}' in generation data")
                        return False
                        
            logger.info(f"Data validation passed for {data_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Bronze data: {str(e)}")
            return False

    def process_bronze_to_silver(self, data_type: str, date_str: str) -> bool:
        """
        Process data from Bronze to Silver layer
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing Bronze to Silver layer for {data_type} on {date_str}")
        
        try:
            # Retrieve Bronze data
            bronze_key = f"{data_type}/bronze/{date_str}.json"
            raw_data = self.bronze_processor.retrieve_bronze_data(bronze_key)
            
            if not raw_data:
                logger.error(f"No Bronze data found for {data_type} on {date_str}")
                return False
                
            # Transform to Silver layer format
            silver_df = self.silver_processor.transform_to_silver(data_type, raw_data)
            
            if silver_df is None or silver_df.empty:
                logger.error(f"No data generated for Silver layer {data_type} on {date_str}")
                return False
                
            # Validate Silver data
            if not self.quality_checker.validate_silver_data(silver_df, data_type):
                logger.error(f"Data validation failed at Silver layer for {data_type}")
                return False
                
            # Store at Silver layer
            silver_key = f"{data_type}/silver/{date_str}.parquet"
            self.silver_processor.store_silver_data(silver_key, silver_df)
            
            logger.info(f"Successfully processed Bronze to Silver for {data_type} on {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Bronze to Silver: {str(e)}")
            return False

    def process_silver_to_gold(self, data_type: str, date_str: str) -> bool:
        """
        Process data from Silver to Gold layer
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing Silver to Gold layer for {data_type} on {date_str}")
        
        try:
            # Retrieve Silver data
            silver_key = f"{data_type}/silver/{date_str}.parquet"
            silver_df = self.silver_processor.retrieve_silver_data(silver_key)
            
            if silver_df is None or silver_df.empty:
                logger.error(f"No Silver data found for {data_type} on {date_str}")
                return False
                
            # Transform to Gold layer format
            gold_df = self.gold_processor.transform_to_gold(data_type, silver_df)
            
            if gold_df is None or gold_df.empty:
                logger.error(f"No data generated for Gold layer {data_type} on {date_str}")
                return False
                
            # Store at Gold layer
            gold_key = f"{data_type}/gold/{date_str}.parquet"
            self.gold_processor.store_gold_data(gold_key, gold_df)
            
            logger.info(f"Successfully processed Silver to Gold for {data_type} on {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Silver to Gold: {str(e)}")
            return False

    def process_bronze_layer(self, data_type: str, date_str: str, raw_data: Dict[str, Any]) -> bool:
        """
        Process data at Bronze layer
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            raw_data: Raw data from ingestion
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing Bronze layer for {data_type} on {date_str}")
        
        # Validate data at Bronze layer
        if not self.quality_checker.validate_bronze_data(raw_data, data_type):
            logger.error(f"Data validation failed at Bronze layer for {data_type}")
            return False
            
        # Process and store at Bronze layer
        try:
            # Store raw data in Bronze layer
            bronze_key = f"{data_type}/bronze/{date_str}.json"
            self.bronze_processor.store_bronze_data(bronze_key, raw_data)
            
            logger.info(f"Successfully stored Bronze data for {data_type} on {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Bronze layer: {str(e)}")
            return False

    def process_silver_layer(self, data_type: str, date_str: str) -> bool:
        """
        Process data at Silver layer
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing Silver layer for {data_type} on {date_str}")
        
        try:
            # Retrieve Bronze data
            bronze_key = f"{data_type}/bronze/{date_str}.json"
            raw_data = self.bronze_processor.retrieve_bronze_data(bronze_key)
            
            if not raw_data:
                logger.error(f"No Bronze data found for {data_type} on {date_str}")
                return False
                
            # Transform to Silver layer format
            silver_df = self.silver_processor.transform_to_silver(data_type, raw_data)
            
            if silver_df is None or silver_df.empty:
                logger.error(f"No data generated for Silver layer {data_type} on {date_str}")
                return False
                
            # Validate Silver data
            if not self.quality_checker.validate_silver_data(silver_df, data_type):
                logger.error(f"Data validation failed at Silver layer for {data_type}")
                return False
                
            # Store at Silver layer
            silver_key = f"{data_type}/silver/{date_str}.parquet"
            self.silver_processor.store_silver_data(silver_key, silver_df)
            
            logger.info(f"Successfully stored Silver data for {data_type} on {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Silver layer: {str(e)}")
            return False

    def process_gold_layer(self, data_type: str, date_str: str) -> bool:
        """
        Process data at Gold layer
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing Gold layer for {data_type} on {date_str}")
        
        try:
            # Retrieve Silver data
            silver_key = f"{data_type}/silver/{date_str}.parquet"
            silver_df = self.silver_processor.retrieve_silver_data(silver_key)
            
            if silver_df is None or silver_df.empty:
                logger.error(f"No Silver data found for {data_type} on {date_str}")
                return False
                
            # Transform to Gold layer format
            gold_df = self.gold_processor.transform_to_gold(data_type, silver_df)
            
            if gold_df is None or gold_df.empty:
                logger.error(f"No data generated for Gold layer {data_type} on {date_str}")
                return False
                
            # Store at Gold layer
            gold_key = f"{data_type}/gold/{date_str}.parquet"
            self.gold_processor.store_gold_data(gold_key, gold_df)
            
            logger.info(f"Successfully stored Gold data for {data_type} on {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing Gold layer: {str(e)}")
            return False

    def process_incremental_data(self, data_type: str, date_str: str, raw_data: Dict[str, Any]) -> bool:
        """
        Process incremental data updates
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            raw_data: Raw data from ingestion
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing incremental data for {data_type} on {date_str}")
        
        # Check if data already exists in Gold layer
        gold_key = f"{data_type}/gold/{date_str}.parquet"
        try:
            self.s3_client.head_object(
                Bucket=self.config.BRONZE_BUCKET,
                Key=gold_key
            )
            logger.info(f"Data already exists in Gold layer for {data_type} on {date_str}")
            return True  # Already processed, no need to reprocess
        except:
            # Data doesn't exist, proceed with processing
            pass
            
        # Process the full pipeline
        return self.process_data_pipeline(data_type, date_str, raw_data)

    def get_data_quality_metrics(self, data_type: str, date_str: str) -> Dict[str, Any]:
        """
        Get quality metrics for processed data
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Dict with quality metrics
        """
        metrics = {
            'data_type': data_type,
            'date': date_str,
            'bronze_processed': False,
            'silver_processed': False,
            'gold_processed': False,
            'processing_timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Check if data already exists in Gold layer
            gold_key = f"{data_type}/gold/{date_str}.parquet"
            try:
                self.s3_client.head_object(
                    Bucket=self.config.BRONZE_BUCKET,
                    Key=gold_key
                )
                metrics['bronze_processed'] = True
            except:
                metrics['bronze_processed'] = False
                
            # Check Silver layer
            silver_key = f"{data_type}/silver/{date_str}.parquet"
            try:
                self.s3_client.head_object(
                    Bucket=self.config.BRONZE_BUCKET,
                    Key=silver_key
                )
                metrics['silver_processed'] = True
            except:
                metrics['silver_processed'] = False
                
            # Check Gold layer
            gold_key = f"{data_type}/gold/{date_str}.parquet"
            try:
                self.s3_client.head_object(
                    Bucket=self.config.BRONZE_BUCKET,
                    Key=gold_key
                )
                metrics['gold_processed'] = True
            except:
                metrics['gold_processed'] = False
                
        except Exception as e:
            logger.error(f"Error getting quality metrics: {str(e)}")
            
        return metrics