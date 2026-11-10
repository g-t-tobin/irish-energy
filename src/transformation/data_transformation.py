"""
Main data transformation pipeline for Bronze/Silver/Gold layers
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import pyarrow as pa
import pyarrow.parquet as pq
from loguru import logger
import boto3
from io import BytesIO
import hashlib

from src.common.config import Config
from src.transformation.quality_checks import QualityChecker
from src.transformation.bronze_layer import BronzeLayerProcessor
from src.transformation.silver_layer import SilverLayerProcessor
from src.transformation.gold_layer import GoldLayerProcessor
from src.transformation.retry_logic import exponential_backoff_retry, RetryConfig, CircuitBreaker, TransformationRetryManager


class DataTransformer:
    """
    Handles data transformation operations
    """

    def __init__(self, s3_client=None):
        self.config = Config()
        self.s3_client = s3_client or boto3.client('s3')
        self.bronze_processor = BronzeLayerProcessor(s3_client)
        self.silver_processor = SilverLayerProcessor()
        self.gold_processor = GoldLayerProcessor()
        self.quality_checker = QualityChecker()
        
        # Initialize retry configurations
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=60.0,
            backoff_factor=2.0
        )
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60.0
        )
        
        # Initialize retry manager
        self.retry_manager = TransformationRetryManager(self.retry_config)
    
    def _execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute an operation with retry logic
        
        Args:
            operation: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation
        """
        # Use the retry manager with circuit breaker
        return self.retry_manager.safe_execute_with_retry(operation, *args, **kwargs)

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

    @exponential_backoff_retry(config=None, circuit_breaker=None)
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
            
            def retrieve_bronze_operation():
                return self.bronze_processor.retrieve_bronze_data(bronze_key)
            
            raw_data = self._execute_with_retry(retrieve_bronze_operation)
            
            if not raw_data:
                logger.error(f"No Bronze data found for {data_type} on {date_str}")
                return False
                
            # Transform to Silver layer format
            def transform_silver_operation():
                return self.silver_processor.transform_to_silver(data_type, raw_data)
            
            silver_df = self._execute_with_retry(transform_silver_operation)
            
            if silver_df is None or silver_df.empty:
                logger.error(f"No data generated for Silver layer {data_type} on {date_str}")
                return False
                
            # Validate Silver data
            if not self.quality_checker.validate_silver_data(silver_df, data_type):
                logger.error(f"Data validation failed at Silver layer for {data_type}")
                return False
                
            # Store at Silver layer
            silver_key = f"{data_type}/silver/{date_str}.parquet"
            
            def store_silver_operation():
                return self.silver_processor.store_silver_data(silver_key, silver_df)
            
            success = self._execute_with_retry(store_silver_operation)
            
            if success:
                logger.info(f"Successfully processed Bronze to Silver for {data_type} on {date_str}")
                return True
            else:
                logger.error(f"Failed to store Silver data for {data_type} on {date_str}")
                return False
            
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
            
            def store_bronze_operation():
                return self.bronze_processor.store_bronze_data(bronze_key, raw_data)
            
            # Execute with retry logic
            success = self._execute_with_retry(store_bronze_operation)
            
            if success:
                logger.info(f"Successfully stored Bronze data for {data_type} on {date_str}")
                return True
            else:
                logger.error(f"Failed to store Bronze data for {data_type} on {date_str}")
                return False
            
        except Exception as e:
            logger.error(f"Error processing Bronze layer: {str(e)}")
            return False

    def process_silver_layer(self, data_type: str, date_str: str) -> bool:
        """
        Process data at Silver layer with idempotency support
        
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
            
            def retrieve_bronze_operation():
                return self.bronze_processor.retrieve_bronze_data(bronze_key)
            
            raw_data = self._execute_with_retry(retrieve_bronze_operation)
            
            if not raw_data:
                logger.error(f"No Bronze data found for {data_type} on {date_str}")
                return False
                
            # Compute input hash for idempotency tracking
            input_hash = self._compute_input_hash(raw_data)
            
            # Check if this transformation has already been performed with same inputs
            # We check at the Silver layer level
            from src.transformation.idempotent_transformation import check_existing_transformation, IdempotentTransformation
            
            def check_existing_operation():
                return check_existing_transformation(
                    self.silver_processor, data_type, date_str, 'silver', input_hash, self.s3_client
                )
            
            exists, existing_transformation_hash = self._execute_with_retry(check_existing_operation)
            
            if exists and existing_transformation_hash:
                logger.info(f"Data already processed with same inputs for {data_type} on {date_str}")
                logger.info(f"Using existing transformation with hash: {existing_transformation_hash}")
                return True  # Already processed with same inputs, no need to reprocess
                
            # Transform to Silver layer format
            def transform_silver_operation():
                return self.silver_processor.transform_to_silver(data_type, raw_data)
            
            silver_df = self._execute_with_retry(transform_silver_operation)
            
            if silver_df is None or silver_df.empty:
                logger.error(f"No data generated for Silver layer {data_type} on {date_str}")
                return False
                
            # Validate Silver data
            if not self.quality_checker.validate_silver_data(silver_df, data_type):
                logger.error(f"Data validation failed at Silver layer for {data_type}")
                return False
                
            # Compute output hash for consistency checks
            output_hash = IdempotentTransformation.compute_dataframe_hash(silver_df)
            
            # Store at Silver layer with metadata for idempotency
            silver_key = f"{data_type}/silver/{date_str}.parquet"
            
            def store_silver_operation():
                return self.silver_processor.store_silver_data(silver_key, silver_df, {
                    'input_hash': input_hash,
                    'output_hash': output_hash,
                    'transformation_type': 'silver',
                    'data_type': data_type,
                    'date': date_str
                })
            
            success = self._execute_with_retry(store_silver_operation)
            
            if success:
                logger.info(f"Successfully stored Silver data for {data_type} on {date_str}")
            else:
                logger.error(f"Failed to store Silver data for {data_type} on {date_str}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing Silver layer: {str(e)}")
            return False

    def process_gold_layer(self, data_type: str, date_str: str) -> bool:
        """
        Process data at Gold layer with idempotency support
        
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
            
            def retrieve_silver_operation():
                return self.silver_processor.retrieve_silver_data(silver_key)
            
            silver_df = self._execute_with_retry(retrieve_silver_operation)
            
            if silver_df is None or silver_df.empty:
                logger.error(f"No Silver data found for {data_type} on {date_str}")
                return False
                
            # Transform to Gold layer format
            def transform_gold_operation():
                return self.gold_processor.transform_to_gold(data_type, silver_df)
            
            gold_df = self._execute_with_retry(transform_gold_operation)
            
            if gold_df is None or gold_df.empty:
                logger.error(f"No data generated for Gold layer {data_type} on {date_str}")
                return False
                
            # Compute output hash for consistency checks
            output_hash = IdempotentTransformation.compute_dataframe_hash(gold_df)
            
            # Store at Gold layer with metadata for idempotency
            gold_key = f"{data_type}/gold/{date_str}.parquet"
            
            def store_gold_operation():
                return self.gold_processor.store_gold_data(gold_key, gold_df, {
                    'input_hash': '',  # This would be computed from the bronze data, but we don't have it here
                    'output_hash': output_hash,
                    'transformation_type': 'gold',
                    'data_type': data_type,
                    'date': date_str
                })
            
            success = self._execute_with_retry(store_gold_operation)
            
            if success:
                logger.info(f"Successfully stored Gold data for {data_type} on {date_str}")
            else:
                logger.error(f"Failed to store Gold data for {data_type} on {date_str}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing Gold layer: {str(e)}")
            return False

    def process_incremental_data(self, data_type: str, date_str: str, raw_data: Dict[str, Any]) -> bool:
        """
        Process incremental data updates with idempotency support
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            raw_data: Raw data from ingestion
             
        Returns:
            bool: True if successful, False otherwise
        """
        from botocore.exceptions import ClientError
        from src.transformation.idempotent_transformation import (
            check_existing_transformation,
            idempotent_store_data,
            IdempotentTransformation
        )
        
        logger.info(f"Processing incremental data for {data_type} on {date_str}")
        
        # Compute input hash for idempotency tracking
        input_hash = self._compute_input_hash(raw_data)
        
        # Check if this transformation has already been performed with same inputs
        # We check at the Gold layer level since that's the final destination
        exists, existing_transformation_hash = check_existing_transformation(
            self.gold_processor, data_type, date_str, 'gold', input_hash, self.s3_client
        )
        
        if exists and existing_transformation_hash:
            logger.info(f"Data already processed with same inputs for {data_type} on {date_str}")
            logger.info(f"Using existing transformation with hash: {existing_transformation_hash}")
            return True  # Already processed with same inputs, no need to reprocess
            
        # Process the full pipeline
        success = self.process_data_pipeline(data_type, date_str, raw_data)
        
        if success:
            # For idempotency, we need to track that this transformation was completed
            # This is handled in the individual layer processing methods now
            pass
            
        return success

    def _compute_input_hash(self, raw_data: Dict[str, Any]) -> str:
        """
        Compute a hash of the raw input data for idempotency tracking
        
        Args:
            raw_data: Raw data dictionary
            
        Returns:
            MD5 hash string of the input data
        """
        # Convert to JSON for consistent hashing
        data_json = json.dumps(raw_data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(data_json.encode('utf-8')).hexdigest()

    def get_data_quality_metrics(self, data_type: str, date_str: str) -> Dict[str, Any]:
        """
        Get quality metrics for processed data
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Dict with quality metrics
        """
        from botocore.exceptions import ClientError
        
        metrics = {
            'data_type': data_type,
            'date': date_str,
            'bronze_processed': False,
            'silver_processed': False,
            'gold_processed': False,
            'processing_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Check if data already exists in Bronze layer
        bronze_key = f"{data_type}/bronze/{date_str}.json"
        try:
            self.s3_client.head_object(
                Bucket=self.config.BRONZE_BUCKET,
                Key=bronze_key
            )
            metrics['bronze_processed'] = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # This is a genuine missing object case - return False
                metrics['bronze_processed'] = False
            else:
                # Re-raise AWS permission errors, network failures, and service errors as they indicate real issues
                raise
            
        # Check Silver layer
        silver_key = f"{data_type}/silver/{date_str}.parquet"
        try:
            self.s3_client.head_object(
                Bucket=self.config.SILVER_BUCKET,
                Key=silver_key
            )
            metrics['silver_processed'] = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # This is a genuine missing object case - return False
                metrics['silver_processed'] = False
            else:
                # Re-raise AWS permission errors, network failures, and service errors as they indicate real issues
                raise
            
        # Check Gold layer
        gold_key = f"{data_type}/gold/{date_str}.parquet"
        try:
            self.s3_client.head_object(
                Bucket=self.config.GOLD_BUCKET,
                Key=gold_key
            )
            metrics['gold_processed'] = True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # This is a genuine missing object case - return False
                metrics['gold_processed'] = False
            else:
                # Re-raise AWS permission errors, network failures, and service errors as they indicate real issues
                raise
            
        return metrics