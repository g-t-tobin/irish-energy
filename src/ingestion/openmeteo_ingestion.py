"""
Open-Meteo weather data ingestion client
Handles HTTP retries, rate limiting, validation, structured logging, and immutable storage
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import boto3
from botocore.exceptions import ClientError
from loguru import logger
import asyncio

from src.common.config import Config
from src.monitoring.service import MonitoringService


class OpenMeteoIngestionClient:
    """Client for ingesting weather data from Open-Meteo API"""

    def __init__(self, config: Config = None):
        """
        Initialize Open-Meteo ingestion client

        Args:
            config: Configuration object (optional, defaults to Config())
        """
        self.config = config or Config()
        self.session = self._create_session()
        self.s3_client = boto3.client('s3', region_name=self.config.AWS_REGION)
        self.monitoring_service = MonitoringService()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()

        # Configure retry strategy with exponential backoff and jitter
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _record_execution_start(self, data_type: str, date_range: str, source: str = "Open-Meteo") -> str:
        """Record the start of an execution and return execution ID"""
        execution_id = self.monitoring_service.record_execution_start(
            data_type=data_type,
            date_str=date_range,
            source=source
        )
        return execution_id

    def _record_execution_success(self, execution_id: str, details: Dict[str, Any]) -> None:
        """Record successful completion of an execution"""
        # Extract data type and date from details
        data_type = details.get('data_type', 'unknown')
        date_str = details.get('date', 'unknown')
        self.monitoring_service.record_execution_success(execution_id, data_type, date_str, "Open-Meteo", 0.0)

    def _record_execution_failure(self, execution_id: str, error: str,
                                  data_type: str = None, date_str: str = None) -> None:
        """Record failed completion of an execution with actual metadata when available"""
        self.monitoring_service.record_execution_failure(execution_id, error, data_type, date_str)

    def _get_api_headers(self) -> Dict[str, str]:
        """Get headers for Open-Meteo API requests"""
        return {
            'Content-Type': 'application/json',
            'User-Agent': 'IrishEnergyAnalytics/1.0',
        }

    def _rate_limit(self, min_delay: float = 0.1, max_delay: float = 0.5) -> None:
        """Apply random delay to respect rate limits"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def fetch_weather_data(self, latitude: float, longitude: float, start_date: str, end_date: str, max_retries: int = 3) -> Optional[Dict[Any, Any]]:
        """
        Fetch weather data for a location and date range from Open-Meteo API

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary containing weather data or None if failed
        """
        # Record execution start
        data_type = "openmeteo"
        date_range = f"{start_date} to {end_date}"
        execution_id = self._record_execution_start(
            data_type=data_type,
            source="Open-Meteo",
            date_range=date_range
        )

        for attempt in range(max_retries + 1):
            try:
                # Open-Meteo API endpoint for historical weather data
                url = f"{self.config.OPEN_METEO_API_URL}/v1/archive"

                # Parameters for weather data request
                params = {
                    'latitude': latitude,
                    'longitude': longitude,
                    'start_date': start_date,
                    'end_date': end_date,
                    'hourly': 'temperature_2m,precipitation,rain,snowfall,wind_speed_10m,relative_humidity_2m',
                    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max',
                    'timezone': 'Europe/Dublin'
                }

                # Add authentication if required (placeholder)
                headers = self._get_api_headers()

                logger.info(f"Fetching weather data for coordinates ({latitude}, {longitude}) from {start_date} to {end_date} (attempt {attempt + 1})")

                # Apply rate limiting
                self._rate_limit()

                # Make request with timeout
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=(self.config.REQUEST_TIMEOUT, self.config.REQUEST_TIMEOUT)
                )

                # Handle retryable status codes
                if response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < max_retries:
                        # Calculate backoff with jitter
                        backoff_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Received {response.status_code} from Open-Meteo API, retrying in {backoff_time:.2f}s")
                        time.sleep(backoff_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for weather data for coordinates ({latitude}, {longitude})")
                        self._record_execution_failure(execution_id, f"Max retries exceeded for coordinates ({latitude}, {longitude})", data_type, date_range)
                        return None

                response.raise_for_status()

                data = response.json()

                # Validate response structure
                if not isinstance(data, dict):
                    logger.warning(f"Unexpected response format for weather data: {type(data)}")
                    self._record_execution_failure(execution_id, f"Unexpected response format for coordinates ({latitude}, {longitude})", data_type, date_range)
                    return None

                # Validate required fields in response
                required_fields = ['latitude', 'longitude', 'timezone', 'hourly', 'daily']
                for field in required_fields:
                    if field not in data:
                        logger.warning(f"Missing required field '{field}' in weather data response")
                        self._record_execution_failure(execution_id, f"Missing required field '{field}' for coordinates ({latitude}, {longitude})", data_type, date_range)
                        return None

                logger.success(f"Successfully fetched weather data for coordinates ({latitude}, {longitude})")

                # Record successful execution
                self._record_execution_success(execution_id, {
                    'data_type': data_type,
                    'date': date_range,
                    'data_points': len(data.get('hourly', {}).get('time', [])),
                    'source': 'Open-Meteo'
                })

                return data

            except requests.exceptions.Timeout:
                logger.error(f"Timeout fetching weather data for coordinates ({latitude}, {longitude}) (attempt {attempt + 1})")
                if attempt < max_retries:
                    backoff_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Retrying in {backoff_time:.2f}s")
                    time.sleep(backoff_time)
                    continue
                self._record_execution_failure(execution_id, f"Timeout for coordinates ({latitude}, {longitude})", data_type, date_range)
                return None
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error fetching weather data for coordinates ({latitude}, {longitude}) (attempt {attempt + 1})")
                if attempt < max_retries:
                    backoff_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Retrying in {backoff_time:.2f}s")
                    time.sleep(backoff_time)
                    continue
                self._record_execution_failure(execution_id, f"Connection error for coordinates ({latitude}, {longitude})", data_type, date_range)
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"HTTP error fetching weather data: {e}")
                self._record_execution_failure(execution_id, f"HTTP error: {str(e)}", data_type, date_range)
                return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for weather data: {e}")
                self._record_execution_failure(execution_id, f"JSON decode error: {str(e)}", data_type, date_range)
                return None
            except Exception as e:
                logger.error(f"Unexpected error fetching weather data: {e}")
                self._record_execution_failure(execution_id, f"Unexpected error: {str(e)}", data_type, date_range)
                return None

    def store_raw_data(self, data: Dict[Any, Any], location: str, date: str) -> bool:
        """
        Store raw weather data in Bronze S3 layer with metadata

        Args:
            data: Raw weather data to store
            location: Location identifier (e.g., cork, dublin, galway)
            date: Date of the data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create key for S3 storage
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            key = f"weather/{location}/{date}/{timestamp}_raw.json"

            # Prepare metadata
            metadata = {
                'source': 'Open-Meteo',
                'location': location,
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

            logger.success(f"Successfully stored raw weather data for {location} on {date} in S3")
            return True

        except ClientError as e:
            logger.error(f"AWS error storing raw weather data: {e}")
            return False
        except Exception as e:
            logger.error(f"Error storing raw weather data: {e}")
            return False

    def ingest_single_day(self, location: str, date: str, max_retries: int = 3) -> bool:
        """
        Ingest weather data for a single day for a specific location

        Args:
            location: Location identifier (cork, dublin, galway)
            date: Date in YYYY-MM-DD format
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting weather ingestion for {location} on {date}")

        # Define coordinates for supported locations
        locations = {
            'cork': {'lat': 51.8985, 'lon': -8.4755},
            'dublin': {'lat': 53.3498, 'lon': -6.2603},
            'galway': {'lat': 53.2707, 'lon': -9.0568}
        }

        if location not in locations:
            logger.error(f"Unsupported location: {location}")
            return False

        coords = locations[location]

        # Fetch weather data
        weather_data = self.fetch_weather_data(
            coords['lat'],
            coords['lon'],
            date,
            date,
            max_retries
        )

        if weather_data:
            success = self.store_raw_data(weather_data, location, date)
            if not success:
                logger.error(f"Failed to store weather data for {location} on {date}")
                return False
            return True
        else:
            logger.error(f"Failed to fetch weather data for {location} on {date}")
            return False

    def ingest_date_range(self, location: str, start_date: str, end_date: str, max_retries: int = 3) -> Dict[str, int]:
        """
        Ingest weather data for a range of dates for a specific location

        Args:
            location: Location identifier (cork, dublin, galway)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            max_retries: Maximum number of retry attempts

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

            if self.ingest_single_day(location, date_str, max_retries):
                stats['successful_days'] += 1
            else:
                stats['failed_days'] += 1

            # Move to next day
            current_date += timedelta(days=1)

        logger.info(f"Weather ingestion complete for {location}. Stats: {stats}")
        return stats


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Open-Meteo ingestion

    Args:
        event: Lambda event data
        context: Lambda context

    Returns:
        Dictionary with ingestion results
    """
    logger.info("Open-Meteo ingestion Lambda invoked")

    # Initialize client
    client = OpenMeteoIngestionClient()

    # Determine date range (default to yesterday)
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    # Use parameters from event if provided
    location = event.get('location', 'dublin')
    date_from_event = event.get('date')

    if date_from_event:
        start_date = date_from_event
        end_date = date_from_event
    else:
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = yesterday.strftime('%Y-%m-%d')

    # Track if ingestion was successful
    stats = {}

    try:
        # Perform ingestion
        stats = client.ingest_date_range(location, start_date, end_date)
        # Determine success based on actual ingestion statistics
        # Success requires at least one day to be successfully ingested
        ingestion_successful = stats.get('successful_days', 0) > 0

    except Exception as e:
        logger.error(f"Error in Open-Meteo ingestion Lambda: {e}")
        # We still want to emit the failure event even if ingestion fails
        ingestion_successful = False
        stats = {'error': str(e)}

    # Emit EventBridge event regardless of success or failure
    try:
        eventbridge_client = boto3.client('events')
        if ingestion_successful:
            eventbridge_client.put_events(
                Entries=[
                    {
                        'Source': 'irish-energy.ingestion',
                        'DetailType': 'OpenMeteo Ingestion Complete',
                        'Detail': json.dumps({
                            'data_type': 'openmeteo',
                            'location': location,
                            'date_range': f'{start_date} to {end_date}',
                            'stats': stats
                        })
                    }
                ]
            )
            logger.info("Successfully emitted Open-Meteo ingestion completion event")
        else:
            eventbridge_client.put_events(
                Entries=[
                    {
                        'Source': 'irish-energy.ingestion',
                        'DetailType': 'OpenMeteo Ingestion Failed',
                        'Detail': json.dumps({
                            'data_type': 'openmeteo',
                            'location': location,
                            'date_range': f'{start_date} to {end_date}',
                            'error': str(stats.get('error', 'Unknown error'))
                        })
                    }
                ]
            )
            logger.info("Successfully emitted Open-Meteo ingestion failure event")
    except Exception as e:
        logger.error(f"Failed to emit Open-Meteo ingestion event: {e}")

    # Return appropriate response based on ingestion outcome
    if ingestion_successful:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Open-Meteo ingestion completed for {location}',
                'stats': stats,
                'date_range': f'{start_date} to {end_date}',
                'location': location
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(stats.get('error', 'Unknown error'))
            })
        }