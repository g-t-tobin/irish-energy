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
            # EirGrid API endpoint for demand data using verified DashboardService endpoint
            url = f"{self.config.EIRGRID_API_URL}/DashboardService.svc/data"

            # Format date for API (dd-MMM-yyyy format) with time components for full day
            target_date = datetime.strptime(date, '%Y-%m-%d')
            formatted_date_from = target_date.strftime('%d-%b-%Y %H:%M')
            formatted_date_to = (target_date + timedelta(days=1)).strftime('%d-%b-%Y %H:%M')

            params = {
                'area': 'demandActual',
                'region': 'ROI',
                'datefrom': formatted_date_from,
                'dateto': formatted_date_to
            }

            # Add authentication if required (placeholder)
            headers = self._get_api_headers()

            logger.info(f"Fetching demand data for {date}")

            # Apply rate limiting
            self._rate_limit()

            response = self.session.get(url, params=params, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            # Diagnostic instrumentation for record loss investigation
            self._diagnose_api_response('demand', response.status_code, data)

            # Validate response structure
            if not isinstance(data, dict):
                logger.warning(f"Unexpected response format for demand data: {type(data)}")
                return None

            # Convert EirGrid API response structure to expected format
            converted_data = self._convert_demand_response(data, date)
            if converted_data is None:
                return None

            logger.success(f"Successfully fetched demand data for {date}")
            return converted_data

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
            # EirGrid API endpoint for generation data using verified DashboardService endpoint
            url = f"{self.config.EIRGRID_API_URL}/DashboardService.svc/data"

            # Format date for API (dd-MMM-yyyy format) with time components for full day
            target_date = datetime.strptime(date, '%Y-%m-%d')
            formatted_date_from = target_date.strftime('%d-%b-%Y %H:%M')
            formatted_date_to = (target_date + timedelta(days=1)).strftime('%d-%b-%Y %H:%M')

            params = {
                'area': 'generationActual',
                'region': 'ROI',
                'datefrom': formatted_date_from,
                'dateto': formatted_date_to
            }

            # Add authentication if required (placeholder)
            headers = self._get_api_headers()

            logger.info(f"Fetching generation data for {date}")

            # Apply rate limiting
            self._rate_limit()

            response = self.session.get(url, params=params, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            # Diagnostic instrumentation for record loss investigation
            self._diagnose_api_response('generation', response.status_code, data)

            # Validate response structure
            if not isinstance(data, dict):
                logger.warning(f"Unexpected response format for generation data: {type(data)}")
                return None

            # Convert EirGrid API response structure to expected format
            converted_data = self._convert_generation_response(data, date)
            if converted_data is None:
                return None

            logger.success(f"Successfully fetched generation data for {date}")
            return converted_data

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching generation data for {date}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for generation data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching generation data for {date}: {e}")
            return None

    def _diagnose_api_response(self, data_type: str, status_code: int, raw_data: Dict[Any, Any]) -> None:
        """
        Diagnostic instrumentation for EirGrid API response analysis

        Args:
            data_type: Either 'demand' or 'generation'
            status_code: HTTP status code from API response
            raw_data: Raw API response data
        """
        logger.info(f"API Response Diagnostics - {data_type.upper()}:")
        logger.info(f"  HTTP Status: {status_code}")

        # Top-level response keys
        if isinstance(raw_data, dict):
            logger.info(f"  Response Keys: {list(raw_data.keys())}")

            # Rows diagnostics
            rows = raw_data.get('Rows', [])
            logger.info(f"  Rows field present: {'Rows' in raw_data}")
            logger.info(f"  Rows data type: {type(rows)}")
            logger.info(f"  Rows count: {len(rows) if isinstance(rows, list) else 'N/A'}")

            if isinstance(rows, list) and len(rows) > 0:
                # Group by FieldName
                field_name_counts = {}
                region_counts = {}
                matching_rows = 0
                rejected_rows = 0
                rejection_reasons = {}
                timestamps = []

                for row in rows:
                    if not isinstance(row, dict):
                        rejected_rows += 1
                        rejection_reasons['malformed_row'] = rejection_reasons.get('malformed_row', 0) + 1
                        continue

                    field_name = row.get('FieldName', 'Unknown')
                    region = row.get('Region', 'Unknown')

                    # Count by FieldName
                    field_name_counts[field_name] = field_name_counts.get(field_name, 0) + 1

                    # Count by Region
                    region_counts[region] = region_counts.get(region, 0) + 1

                    # Check matching criteria
                    is_matching = False
                    if data_type == 'demand':
                        # Demand matching criteria
                        if 'DEMAND' in field_name.upper() and region.upper() == 'ROI':
                            is_matching = True
                    elif data_type == 'generation':
                        # Generation matching criteria (same as in _convert_generation_response)
                        is_generation_field = (
                            'generation' in field_name.lower() and
                            'actual' in field_name.lower() and
                            region.upper() == 'ROI'
                        )
                        if not is_generation_field:
                            gen_indicators = ['Generation', 'Gen', 'Power']
                            region_indicators = ['ROI', 'Republic of Ireland']
                            is_generation_field = (
                                any(indicator.lower() in field_name.lower() for indicator in gen_indicators) and
                                any(indicator.upper() in region.upper() for indicator in region_indicators)
                            )
                        is_matching = is_generation_field

                    if is_matching:
                        matching_rows += 1
                        # Extract timestamp for later analysis
                        effective_time = row.get('EffectiveTime', '')
                        if effective_time:
                            timestamps.append(effective_time)
                    else:
                        rejected_rows += 1
                        # Log rejection reasons
                        if data_type == 'demand':
                            if 'DEMAND' not in field_name.upper():
                                rejection_reasons['field_name_mismatch'] = rejection_reasons.get('field_name_mismatch', 0) + 1
                            if region.upper() != 'ROI':
                                rejection_reasons['region_mismatch'] = rejection_reasons.get('region_mismatch', 0) + 1
                        else:  # generation
                            if 'generation' not in field_name.lower() and 'actual' not in field_name.lower():
                                rejection_reasons['field_name_mismatch'] = rejection_reasons.get('field_name_mismatch', 0) + 1
                            if region.upper() != 'ROI':
                                rejection_reasons['region_mismatch'] = rejection_reasons.get('region_mismatch', 0) + 1

                logger.info(f"  Matching rows: {matching_rows}")
                logger.info(f"  Rejected rows: {rejected_rows}")
                logger.info(f"  Rejection reasons: {rejection_reasons}")
                logger.info(f"  Field name distribution: {field_name_counts}")
                logger.info(f"  Region distribution: {region_counts}")

                if timestamps:
                    # Find first and last timestamps
                    timestamps.sort()
                    first_timestamp = timestamps[0] if timestamps else 'N/A'
                    last_timestamp = timestamps[-1] if timestamps else 'N/A'
                    logger.info(f"  First timestamp: {first_timestamp}")
                    logger.info(f"  Last timestamp: {last_timestamp}")

                    # Check for duplicates
                    if len(timestamps) != len(set(timestamps)):
                        duplicate_count = len(timestamps) - len(set(timestamps))
                        logger.info(f"  Duplicate timestamps: {duplicate_count}")

        else:
            logger.warning(f"Raw data is not a dictionary: {type(raw_data)}")

    def _convert_demand_response(self, raw_data: Dict[Any, Any], date: str) -> Optional[Dict[Any, Any]]:
        """
        Convert EirGrid API response structure to expected internal format

        Args:
            raw_data: Raw API response data
            date: Date string for the data

        Returns:
            Converted data in expected format or None if invalid
        """
        try:
            # Handle different response formats from EirGrid API
            # Expected structure: { "Rows": [ { "FieldName": "...", "Region": "...", "Value": "...", "EffectiveTime": "..." } ] }

            # Check if we have Rows field (typical EirGrid API response)
            rows = raw_data.get('Rows', [])
            if not isinstance(rows, list):
                logger.warning(f"Unexpected Rows format in demand response: {type(rows)}")
                return None

            # Extract demand data points
            demand_values = []
            for row in rows:
                if not isinstance(row, dict):
                    continue

                # Look for demand-related fields
                field_name = row.get('FieldName', '').upper()
                if 'DEMAND' in field_name and row.get('Region', '').upper() == 'ROI':
                    try:
                        # Convert the value to numeric
                        value = float(row.get('Value', 0))
                        # Extract timestamp from EffectiveTime
                        effective_time = row.get('EffectiveTime', '')

                        # Create a data point with timestamp and value
                        demand_values.append({
                            'timestamp': effective_time,
                            'value': value
                        })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse demand value: {row.get('Value', '')}, error: {e}")
                        continue

            # Return data in expected format
            return {
                'date': date,
                'demand': demand_values
            }

        except Exception as e:
            logger.error(f"Error converting demand response: {e}")
            return None

    def _convert_generation_response(self, raw_data: Dict[Any, Any], date: str) -> Optional[Dict[Any, Any]]:
        """
        Convert EirGrid API response structure to expected internal format

        Args:
            raw_data: Raw API response data
            date: Date string for the data

        Returns:
            Converted data in expected format or None if invalid
        """
        try:
            # Handle different response formats from EirGrid API
            # Expected structure: { "Rows": [ { "FieldName": "...", "Region": "...", "Value": "...", "EffectiveTime": "..." } ] }

            # Check if we have Rows field (typical EirGrid API response)
            rows = raw_data.get('Rows', [])
            if not isinstance(rows, list):
                logger.warning(f"Unexpected Rows format in generation response: {type(rows)}")
                return None

            # Extract generation data points
            generation_values = []
            for row in rows:
                if not isinstance(row, dict):
                    continue

                # Look for generation-related fields - be more flexible with field name matching
                field_name = row.get('FieldName', '')
                region = row.get('Region', '')

                # More robust field name matching for EirGrid API
                # Check if this row represents generation data (case insensitive)
                is_generation_field = (
                    'generation' in field_name.lower() and
                    'actual' in field_name.lower() and
                    region.upper() == 'ROI'
                )

                # Alternative: Check for broader generation indicators
                if not is_generation_field:
                    # Check for other generation-related field names that might appear
                    gen_indicators = ['Generation', 'Gen', 'Power']
                    region_indicators = ['ROI', 'Republic of Ireland']
                    is_generation_field = (
                        any(indicator.lower() in field_name.lower() for indicator in gen_indicators) and
                        any(indicator.upper() in region.upper() for indicator in region_indicators)
                    )

                if is_generation_field:
                    try:
                        # Convert the value to numeric
                        value = float(row.get('Value', 0))
                        # Extract timestamp from EffectiveTime
                        effective_time = row.get('EffectiveTime', '')

                        # Create a data point with timestamp and value
                        generation_values.append({
                            'timestamp': effective_time,
                            'value': value
                        })
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse generation value: {row.get('Value', '')}, error: {e}")
                        continue

            # Return data in expected format
            return {
                'date': date,
                'generation': generation_values
            }

        except Exception as e:
            logger.error(f"Error converting generation response: {e}")
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
        demand_success = False
        demand_has_valid_records = False
        if demand_data:
            # Check if demand data has actual records (not just empty lists)
            demand_records = demand_data.get('demand', [])
            if len(demand_records) > 0:  # Only consider it successful if there are actual records
                demand_has_valid_records = True
                success = self.store_raw_data(demand_data, 'demand', date)
                if not success:
                    logger.error(f"Failed to store demand data for {date}")
                    return False
                demand_success = True
            else:
                logger.warning(f"Demand data for {date} contains no records")

        # Fetch generation data
        generation_data = self.fetch_generation_data(date)
        generation_success = False
        generation_has_valid_records = False
        if generation_data:
            # Check if generation data has actual records (not just empty lists)
            generation_records = generation_data.get('generation', [])
            if len(generation_records) > 0:  # Only consider it successful if there are actual records
                generation_has_valid_records = True
                success = self.store_raw_data(generation_data, 'generation', date)
                if not success:
                    logger.error(f"Failed to store generation data for {date}")
                    return False
                generation_success = True
            else:
                logger.warning(f"Generation data for {date} contains no records")

        # Determine overall success based on whether we have valid records
        # SUCCESS: Both sources have valid records (non-empty lists)
        # PARTIAL_SUCCESS: At least one source has valid records
        # FAILED: Neither source has valid records
        if demand_has_valid_records and generation_has_valid_records:
            logger.info(f"Completed ingestion for {date} - SUCCESS: Both demand and generation data with records")
            return True
        elif demand_has_valid_records or generation_has_valid_records:
            logger.info(f"Completed ingestion for {date} - PARTIAL_SUCCESS: One data source with records")
            return True
        elif not demand_success and not generation_success:
            # Both sources failed to return data with records
            logger.warning(f"No valid data successfully fetched for {date}")
            return False
        else:
            # This case shouldn't happen with the current logic but keeping for safety
            logger.info(f"Completed ingestion for {date} - MIXED_RESULT")
            return True

    def ingest_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
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
            'partial_success_days': 0,
            'total_days': 0,
            'detailed_results': []
        }

        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        current_date = start
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            stats['total_days'] += 1

            # Track individual day results
            day_result = {
                'date': date_str,
                'status': 'unknown'
            }

            if self.ingest_single_day(date_str):
                # Check if this was partial success or full success
                # We can't easily distinguish here without changing the ingest_single_day signature
                # So we'll classify based on the boolean return
                day_result['status'] = 'success'
                stats['successful_days'] += 1
            else:
                day_result['status'] = 'failed'
                stats['failed_days'] += 1

            stats['detailed_results'].append(day_result)

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

        # Emit EventBridge event based on ingestion outcome
        # We'll emit a completion event for any ingestion attempt (even if partial or failed)
        # The transformation pipeline will need to handle partial/failed cases appropriately
        try:
            eventbridge_client = boto3.client('events')
            eventbridge_client.put_events(
                Entries=[
                    {
                        'Source': 'irish-energy.ingestion',
                        'DetailType': 'EirGrid Ingestion Complete',
                        'Detail': json.dumps({
                            'data_type': 'eirgrid',
                            'date_range': f'{start_date} to {end_date}',
                            'stats': stats,
                            'ingestion_status': 'completed'  # This will help transformation distinguish successful vs failed
                        })
                    }
                ]
            )
            logger.info("Successfully emitted EirGrid ingestion completion event")
        except Exception as e:
            logger.error(f"Failed to emit EirGrid ingestion event: {e}")

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
        # Even on error, we still emit the event to maintain consistent behavior
        try:
            eventbridge_client = boto3.client('events')
            eventbridge_client.put_events(
                Entries=[
                    {
                        'Source': 'irish-energy.ingestion',
                        'DetailType': 'EirGrid Ingestion Failed',
                        'Detail': json.dumps({
                            'data_type': 'eirgrid',
                            'date_range': f'{start_date} to {end_date}',
                            'error': str(e),
                            'ingestion_status': 'failed'
                        })
                    }
                ]
            )
            logger.info("Successfully emitted EirGrid ingestion failure event")
        except Exception as e2:
            logger.error(f"Failed to emit EirGrid ingestion failure event: {e2}")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }