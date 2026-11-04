"""
EirGrid electricity data ingestion client
Handles HTTP retries, rate limiting, validation, structured logging, and immutable storage
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from src.common.config import Config


class EirGridIngestionClient:
    """Client for ingesting data from EirGrid API"""
    
    def __init__(self, config: Config = None):
        """
        Initialize EirGrid ingestion client
        
        Args:
            config: Configuration object (optional, defaults to Config())
        """
        self.config = config or Config()
        self.session = self._create_session()
        self.s3_client = boto3.client('s3', region_name=self.config.AWS_REGION)
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_api_headers(self) -> Dict[str, str]:
        """Get headers for EirGrid API requests"""
        return {
            'Content-Type': 'application/json',
            'User-Agent': 'IrishEnergyAnalytics/1.0',
        }
    
    def _rate_limit(self, min_delay: float = 0.1, max_delay: float = 0.5) -> None:
        """Apply random delay to respect rate limits"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def fetch_demand_data(self, date: str) -> Optional[Dict[Any, Any]]:
        """
        Fetch demand data for a specific date from EirGrid API
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing demand data or None if failed
        """
        try:
            # EirGrid API endpoint for demand data
            url = f"{self.config.EIRGRID_API_URL}/demand"
            
            params = {
                'date': date,
                'format': 'json'
            }
            
            # Add authentication if required (placeholder)
            headers = self._get_api_headers()
            
            logger.info(f"Fetching demand data for {date}")
            
            # Apply rate limiting
            self._rate_limit()
            
            response = self.session.get(url, params=params, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate response structure
            if not isinstance(data, dict):
                logger.warning(f"Unexpected response format for demand data: {type(data)}")
                return None
                
            logger.success(f"Successfully fetched demand data for {date}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching demand data for {date}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for demand data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching demand data for {date}: {e}")
            return None
    
    def fetch_generation_data(self, date: str) -> Optional[Dict[Any, Any]]:
        """
        Fetch generation data for a specific date from EirGrid API
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary containing generation data or None if failed
        """
        try:
            # EirGrid API endpoint for generation data
            url = f"{self.config.EIRGRID_API_URL}/generation"
            
            params = {
                'date': date,
                'format': 'json'
            }
            
            # Add authentication if required (placeholder)
            headers = self._get_api_headers()
            
            logger.info(f"Fetching generation data for {date}")
            
            # Apply rate limiting
            self._rate_limit()
            
            response = self.session.get(url, params=params, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate response structure
            if not isinstance(data, dict):
                logger.warning(f"Unexpected response format for generation data: {type(data)}")
                return None
                
            logger.success(f"Successfully fetched generation data for {date}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching generation data for {date}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for generation data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching generation data for {date}: {e}")
            return None
    
    def store_raw_data(self, data: Dict[Any, Any], data_type: str, date: str) -> bool:
        """
        Store raw data in Bronze S3 layer with metadata
        
        Args:
            data: Raw data to store
            data_type: Type of data (demand, generation)
            date: Date of the data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create key for S3 storage
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            key = f"{data_type}/{date}/{timestamp}_raw.json"
            
            # Prepare metadata
            metadata = {
                'source': 'EirGrid',
                'data_type': data_type,
                'date': date,
                'timestamp': timestamp,
                'version': '1.0',
                'ingestion_status': 'success'
            }
            
            # Convert data to JSON string
            json_data = json.dumps(data, indent=2)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.config.BRONZE_BUCKET,
                Key=key,
                Body=json_data,
                Metadata=metadata
            )
            
            logger.success(f"Successfully stored raw {data_type} data for {date} in S3")
            return True
            
        except ClientError as e:
            logger.error(f"AWS error storing raw data: {e}")
            return False
        except Exception as e:
            logger.error(f"Error storing raw data: {e}")
            return False
    
    def ingest_single_day(self, date: str) -> bool:
        """
        Ingest data for a single day from EirGrid
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting ingestion for {date}")
        
        # Fetch demand data
        demand_data = self.fetch_demand_data(date)
        if demand_data:
            success = self.store_raw_data(demand_data, 'demand', date)
            if not success:
                logger.error(f"Failed to store demand data for {date}")
                return False
        
        # Fetch generation data  
        generation_data = self.fetch_generation_data(date)
        if generation_data:
            success = self.store_raw_data(generation_data, 'generation', date)
            if not success:
                logger.error(f"Failed to store generation data for {date}")
                return False
                
        logger.info(f"Completed ingestion for {date}")
        return True
    
    def ingest_date_range(self, start_date: str, end_date: str) -> Dict[str, int]:
        """
        Ingest data for a range of dates
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with ingestion statistics
        """
        stats = {
            'successful_days': 0,
            'failed_days': 0,
            'total_days': 0
        }
        
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            stats['total_days'] += 1
            
            if self.ingest_single_day(date_str):
                stats['successful_days'] += 1
            else:
                stats['failed_days'] += 1
                
            # Move to next day
            current_date += timedelta(days=1)
            
        logger.info(f"Ingestion complete. Stats: {stats}")
        return stats


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for EirGrid ingestion
    
    Args:
        event: Lambda event data
        context: Lambda context
        
    Returns:
        Dictionary with ingestion results
    """
    logger.info("EirGrid ingestion Lambda invoked")
    
    try:
        # Initialize client
        client = EirGridIngestionClient()
        
        # Determine date range (default to yesterday)
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Use date from event if provided, otherwise default to yesterday
        date_from_event = event.get('date')
        if date_from_event:
            start_date = date_from_event
            end_date = date_from_event
        else:
            start_date = yesterday.strftime('%Y-%m-%d')
            end_date = yesterday.strftime('%Y-%m-%d')
        
        # Perform ingestion
        stats = client.ingest_date_range(start_date, end_date)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'EirGrid ingestion completed',
                'stats': stats,
                'date_range': f'{start_date} to {end_date}'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in EirGrid ingestion Lambda: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }