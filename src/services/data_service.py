"""
Data service for accessing Gold layer data
"""

import boto3
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO
from typing import Optional, List, Dict, Any
from loguru import logger
import re
from datetime import datetime

from src.common.config import Config


# Define custom exceptions for data access errors
class GoldDataAccessError(Exception):
    """Base exception for Gold layer data access errors"""
    pass


class GoldDataNotFoundError(GoldDataAccessError):
    """Exception raised when Gold layer data is not found"""
    pass


class GoldDataParseError(GoldDataAccessError):
    """Exception raised when Gold layer data parsing fails"""
    pass


class GoldDataValidationError(GoldDataAccessError):
    """Exception raised when Gold layer data validation fails"""
    pass


class S3GoldDataRetriever:
    """Retrieves data from Gold layer in S3"""

    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.s3_client = boto3.client('s3', region_name=self.config.AWS_REGION)

    def get_demand_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get demand data from Gold layer"""
        # Validate date format if provided
        if start_date and not self._is_valid_date_format(start_date):
            raise GoldDataValidationError(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD")
        if end_date and not self._is_valid_date_format(end_date):
            raise GoldDataValidationError(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD")

        try:
            # Build the S3 prefix for demand data (following pattern: gold/demand/date.parquet)
            prefix = f"{self.config.GOLD_PREFIX}demand/"
            
            # Get objects from S3 bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.config.GOLD_BUCKET, Prefix=prefix)
            
            # Collect all matching parquet files
            parquet_files = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Filter by date range if provided
                        if self._is_in_date_range(obj['Key'], start_date, end_date):
                            parquet_files.append(obj['Key'])
            
            # Sort files by date (ascending order to get oldest first)
            parquet_files.sort()
            
            # Read and concatenate data from all matching files
            dataframes = []
            for file_key in parquet_files:
                try:
                    response = self.s3_client.get_object(Bucket=self.config.GOLD_BUCKET, Key=file_key)
                    data = response['Body'].read()
                    table = pq.read_table(BytesIO(data))
                    df = table.to_pandas()
                    dataframes.append(df)
                except Exception as e:
                    logger.warning(f"Failed to read parquet file {file_key}: {e}")
                    continue
            
            # Concatenate all dataframes
            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                # Convert timestamp column to datetime if needed
                if 'timestamp' in combined_df.columns:
                    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                # Filter by date range
                if start_date:
                    combined_df = combined_df[combined_df['timestamp'] >= start_date]
                if end_date:
                    combined_df = combined_df[combined_df['timestamp'] <= end_date]
                return combined_df.to_dict('records')
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving demand data: {e}")
            # Re-raise validation errors to maintain expected behavior
            if isinstance(e, GoldDataValidationError):
                raise
            return []

    def get_generation_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get generation data from Gold layer"""
        # Validate date format if provided
        if start_date and not self._is_valid_date_format(start_date):
            raise GoldDataValidationError(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD")
        if end_date and not self._is_valid_date_format(end_date):
            raise GoldDataValidationError(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD")

        try:
            # Build the S3 prefix for generation data (following pattern: gold/generation/date.parquet)
            prefix = f"{self.config.GOLD_PREFIX}generation/"
            
            # Get objects from S3 bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.config.GOLD_BUCKET, Prefix=prefix)
            
            # Collect all matching parquet files
            parquet_files = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Filter by date range if provided
                        if self._is_in_date_range(obj['Key'], start_date, end_date):
                            parquet_files.append(obj['Key'])
            
            # Sort files by date (ascending order to get oldest first)
            parquet_files.sort()
            
            # Read and concatenate data from all matching files
            dataframes = []
            for file_key in parquet_files:
                try:
                    response = self.s3_client.get_object(Bucket=self.config.GOLD_BUCKET, Key=file_key)
                    data = response['Body'].read()
                    table = pq.read_table(BytesIO(data))
                    df = table.to_pandas()
                    dataframes.append(df)
                except Exception as e:
                    logger.warning(f"Failed to read parquet file {file_key}: {e}")
                    continue
            
            # Concatenate all dataframes
            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                # Convert timestamp column to datetime if needed
                if 'timestamp' in combined_df.columns:
                    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                # Filter by date range
                if start_date:
                    combined_df = combined_df[combined_df['timestamp'] >= start_date]
                if end_date:
                    combined_df = combined_df[combined_df['timestamp'] <= end_date]
                return combined_df.to_dict('records')
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving generation data: {e}")
            # Re-raise validation errors to maintain expected behavior
            if isinstance(e, GoldDataValidationError):
                raise
            return []

    def get_weather_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get weather data from Gold layer"""
        # Validate date format if provided
        if start_date and not self._is_valid_date_format(start_date):
            raise GoldDataValidationError(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD")
        if end_date and not self._is_valid_date_format(end_date):
            raise GoldDataValidationError(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD")

        try:
            # Build the S3 prefix for weather data (following pattern: gold/weather/date.parquet)
            prefix = f"{self.config.GOLD_PREFIX}weather/"
            
            # Get objects from S3 bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.config.GOLD_BUCKET, Prefix=prefix)
            
            # Collect all matching parquet files
            parquet_files = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        # Filter by date range if provided
                        if self._is_in_date_range(obj['Key'], start_date, end_date):
                            parquet_files.append(obj['Key'])
            
            # Sort files by date (ascending order to get oldest first)
            parquet_files.sort()
            
            # Read and concatenate data from all matching files
            dataframes = []
            for file_key in parquet_files:
                try:
                    response = self.s3_client.get_object(Bucket=self.config.GOLD_BUCKET, Key=file_key)
                    data = response['Body'].read()
                    table = pq.read_table(BytesIO(data))
                    df = table.to_pandas()
                    dataframes.append(df)
                except Exception as e:
                    logger.warning(f"Failed to read parquet file {file_key}: {e}")
                    continue
            
            # Concatenate all dataframes
            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                # Convert timestamp column to datetime if needed
                if 'timestamp' in combined_df.columns:
                    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                # Filter by date range
                if start_date:
                    combined_df = combined_df[combined_df['timestamp'] >= start_date]
                if end_date:
                    combined_df = combined_df[combined_df['timestamp'] <= end_date]
                return combined_df.to_dict('records')
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving weather data: {e}")
            # Re-raise validation errors to maintain expected behavior
            if isinstance(e, GoldDataValidationError):
                raise
            return []
    
    def _is_valid_date_format(self, date_string: str) -> bool:
        """Check if date string is in valid YYYY-MM-DD format"""
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _is_in_date_range(self, file_key: str, start_date: Optional[str], end_date: Optional[str]) -> bool:
        """Check if a file's date falls within the specified date range"""
        try:
            # Extract date from filename (following pattern: gold/dataset/2023-01-01.parquet)
            # Split by '/' and extract the date part from the third element
            parts = file_key.split('/')
            if len(parts) >= 3:
                filename = parts[-1]  # Get the last part which should be the filename
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                if date_match:
                    file_date_str = date_match.group(1)
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                    
                    if start_date:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        if file_date < start_dt:
                            return False
                            
                    if end_date:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        if file_date > end_dt:
                            return False
                            
                    return True
            # If we can't extract a valid date, include the file by default
            return True
        except Exception:
            # If we can't parse the date, include the file by default
            return True

    def get_quality_metrics(self) -> List[Dict[str, Any]]:
        """Calculate quality metrics for all available datasets in Gold layer"""
        try:
            # Define all possible datasets
            datasets = ['demand', 'generation', 'weather']
            metrics = []
            
            # Track which datasets are available
            available_datasets = []
            
            for dataset_type in datasets:
                try:
                    # Build the S3 prefix for this dataset (following pattern: gold/dataset/date.parquet)
                    prefix = f"{self.config.GOLD_PREFIX}{dataset_type}/"
                    
                    # Get objects from S3 bucket
                    paginator = self.s3_client.get_paginator('list_objects_v2')
                    pages = paginator.paginate(Bucket=self.config.GOLD_BUCKET, Prefix=prefix)
                    
                    # Collect all matching parquet files
                    parquet_files = []
                    last_updated = None
                    
                    for page in pages:
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                parquet_files.append(obj)
                    
                    if parquet_files:
                        available_datasets.append(dataset_type)
                        
                        # Find the most recently updated file to determine last updated time
                        latest_file = max(parquet_files, key=lambda x: x['LastModified'])
                        last_updated = latest_file['LastModified']
                        
                        # Read sample data to calculate quality metrics
                        try:
                            # Read the first file for quality metrics (we'll take the most recent one)
                            file_key = latest_file['Key']
                            response = self.s3_client.get_object(Bucket=self.config.GOLD_BUCKET, Key=file_key)
                            data = response['Body'].read()
                            table = pq.read_table(BytesIO(data))
                            df = table.to_pandas()
                            
                            # Calculate metrics
                            total_records = len(df)
                            missing_values = df.isnull().sum().sum()
                            
                            # Calculate quality score (percentage of non-missing values)
                            total_cells = total_records * len(df.columns) if total_records > 0 else 1
                            quality_score = round((1 - (missing_values / total_cells)) * 100, 2) if total_cells > 0 else 100.0
                            
                            metrics.append({
                                "dataset_name": dataset_type,
                                "total_records": total_records,
                                "missing_values": missing_values,
                                "data_quality_score": quality_score,
                                "last_updated": last_updated
                            })
                        except Exception as e:
                            logger.warning(f"Failed to read sample data for {dataset_type}: {e}")
                            # Even if we can't read data, still include basic info
                            metrics.append({
                                "dataset_name": dataset_type,
                                "total_records": 0,
                                "missing_values": 0,
                                "data_quality_score": 0.0,
                                "last_updated": last_updated
                            })
                    else:
                        # Dataset not found in Gold layer
                        metrics.append({
                            "dataset_name": dataset_type,
                            "total_records": 0,
                            "missing_values": 0,
                            "data_quality_score": 0.0,
                            "last_updated": None
                        })
                        
                except Exception as e:
                    logger.warning(f"Error processing {dataset_type} metrics: {e}")
                    metrics.append({
                        "dataset_name": dataset_type,
                        "total_records": 0,
                        "missing_values": 0,
                        "data_quality_score": 0.0,
                        "last_updated": None
                    })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            # Return minimal metrics in case of failure
            return [
                {"dataset_name": "demand", "total_records": 0, "missing_values": 0, "data_quality_score": 0.0, "last_updated": None},
                {"dataset_name": "generation", "total_records": 0, "missing_values": 0, "data_quality_score": 0.0, "last_updated": None},
                {"dataset_name": "weather", "total_records": 0, "missing_values": 0, "data_quality_score": 0.0, "last_updated": None}
            ]

    def get_summary_data(self) -> Dict[str, Any]:
        """Calculate summary data for all datasets in Gold layer"""
        try:
            # Define all possible datasets
            datasets = ['demand', 'generation', 'weather']
            summary = {
                "total_datasets": 0,
                "total_records": 0,
                "last_updated": None,
                "data_quality_summary": {
                    "total_missing_values": 0,
                    "overall_quality_score": 0.0,
                    "missing_datasets": [],
                    "datasets": {}
                }
            }
            
            # Track which datasets are available
            available_datasets = []
            total_missing_values = 0
            total_records = 0
            dataset_metrics = []
            last_updated = None
            
            for dataset_type in datasets:
                try:
                    # Build the S3 prefix for this dataset (following pattern: gold/dataset/date.parquet)
                    prefix = f"{self.config.GOLD_PREFIX}{dataset_type}/"
                    
                    # Get objects from S3 bucket
                    paginator = self.s3_client.get_paginator('list_objects_v2')
                    pages = paginator.paginate(Bucket=self.config.GOLD_BUCKET, Prefix=prefix)
                    
                    # Collect all matching parquet files
                    parquet_files = []
                    dataset_last_updated = None
                    
                    for page in pages:
                        if 'Contents' in page:
                            for obj in page['Contents']:
                                parquet_files.append(obj)
                    
                    if parquet_files:
                        available_datasets.append(dataset_type)
                        
                        # Find the most recently updated file to determine last updated time
                        latest_file = max(parquet_files, key=lambda x: x['LastModified'])
                        dataset_last_updated = latest_file['LastModified']
                        
                        # Update overall last updated time
                        if last_updated is None or dataset_last_updated > last_updated:
                            last_updated = dataset_last_updated
                        
                        # Read sample data to calculate summary metrics
                        try:
                            # Read the most recent file for summary metrics
                            file_key = latest_file['Key']
                            response = self.s3_client.get_object(Bucket=self.config.GOLD_BUCKET, Key=file_key)
                            data = response['Body'].read()
                            table = pq.read_table(BytesIO(data))
                            df = table.to_pandas()
                            
                            # Calculate summary metrics
                            dataset_records = len(df)
                            dataset_missing_values = df.isnull().sum().sum()
                            
                            # Calculate quality score (percentage of non-missing values)
                            total_cells = dataset_records * len(df.columns) if dataset_records > 0 else 1
                            quality_score = round((1 - (dataset_missing_values / total_cells)) * 100, 2) if total_cells > 0 else 100.0
                            
                            # Store dataset-specific metrics
                            dataset_metrics.append({
                                "dataset_name": dataset_type,
                                "total_records": dataset_records,
                                "missing_values": dataset_missing_values,
                                "data_quality_score": quality_score
                            })
                            
                            # Update totals
                            total_records += dataset_records
                            total_missing_values += dataset_missing_values
                            
                            # Store in summary
                            summary["data_quality_summary"]["datasets"][dataset_type] = {
                                "total_records": dataset_records,
                                "missing_values": dataset_missing_values,
                                "data_quality_score": quality_score
                            }
                            
                        except Exception as e:
                            logger.warning(f"Failed to read sample data for {dataset_type}: {e}")
                            # Even if we can't read data, still include basic info
                            dataset_metrics.append({
                                "dataset_name": dataset_type,
                                "total_records": 0,
                                "missing_values": 0,
                                "data_quality_score": 0.0
                            })
                            summary["data_quality_summary"]["datasets"][dataset_type] = {
                                "total_records": 0,
                                "missing_values": 0,
                                "data_quality_score": 0.0
                            }
                    else:
                        # Dataset not found in Gold layer
                        summary["data_quality_summary"]["datasets"][dataset_type] = {
                            "total_records": 0,
                            "missing_values": 0,
                            "data_quality_score": 0.0
                        }
                        
                except Exception as e:
                    logger.warning(f"Error processing {dataset_type} summary: {e}")
                    summary["data_quality_summary"]["datasets"][dataset_type] = {
                        "total_records": 0,
                        "missing_values": 0,
                        "data_quality_score": 0.0
                    }
            
            # Set summary values
            summary["total_datasets"] = len(available_datasets)
            summary["total_records"] = total_records
            summary["last_updated"] = last_updated
            
            # Calculate overall quality score
            if total_records > 0:
                # We need to calculate total cells properly
                total_cells = 0
                for metric in dataset_metrics:
                    if metric.get("total_records", 0) > 0:
                        # Get the number of columns from the first sample file for each dataset
                        try:
                            # Get a sample file to determine column count
                            prefix = f"{metric['dataset_name']}/{self.config.GOLD_PREFIX}"
                            paginator = self.s3_client.get_paginator('list_objects_v2')
                            pages = paginator.paginate(Bucket=self.config.GOLD_BUCKET, Prefix=prefix)
                            sample_files = []
                            for page in pages:
                                if 'Contents' in page:
                                    sample_files.extend(page['Contents'])
                            if sample_files:
                                sample_file = max(sample_files, key=lambda x: x['LastModified'])
                                response = self.s3_client.get_object(Bucket=self.config.GOLD_BUCKET, Key=sample_file['Key'])
                                data = response['Body'].read()
                                table = pq.read_table(BytesIO(data))
                                df = table.to_pandas()
                                total_cells += metric["total_records"] * len(df.columns)
                        except:
                            # Fallback to a conservative estimate if we can't determine column count
                            total_cells += metric["total_records"] * 10  # Estimate 10 columns average
                
                if total_cells > 0:
                    summary["data_quality_summary"]["overall_quality_score"] = round(
                        (1 - (total_missing_values / total_cells)) * 100, 2
                    )
                else:
                    summary["data_quality_summary"]["overall_quality_score"] = 100.0
            else:
                summary["data_quality_summary"]["overall_quality_score"] = 0.0
            
            # Set missing datasets
            summary["data_quality_summary"]["missing_datasets"] = [
                ds for ds in datasets if ds not in available_datasets
            ]
            
            # Set total missing values
            summary["data_quality_summary"]["total_missing_values"] = total_missing_values
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating summary data: {e}")
            # Return minimal summary in case of failure
            return {
                "total_datasets": 0,
                "total_records": 0,
                "last_updated": None,
                "data_quality_summary": {
                    "total_missing_values": 0,
                    "overall_quality_score": 0.0,
                    "missing_datasets": ["demand", "generation", "weather"],
                    "datasets": {
                        "demand": {"total_records": 0, "missing_values": 0, "data_quality_score": 0.0},
                        "generation": {"total_records": 0, "missing_values": 0, "data_quality_score": 0.0},
                        "weather": {"total_records": 0, "missing_values": 0, "data_quality_score": 0.0}
                    }
                }
            }