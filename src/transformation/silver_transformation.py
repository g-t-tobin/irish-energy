"""
Silver transformation pipeline for Bronze data processing
"""

import os
import json
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import uuid
import hashlib
from loguru import logger

from src.common.config import Config
from src.transformation.quality_checks import QualityChecker
from src.storage.bronze_storage import BronzeStorageFactory


class TransformationStatus(Enum):
    """Status indicators for transformation operations"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"


class QuarantineReason(Enum):
    """Reasons for quarantining records"""
    MISSING_VALUE = "missing_value"
    INVALID_NUMERIC = "invalid_numeric"
    INVALID_TIMESTAMP = "invalid_timestamp"
    DUPLICATE_DETECTED = "duplicate_detected"
    SCHEMA_VIOLATION = "schema_violation"
    DATA_TYPE_ERROR = "data_type_error"
    UNEXPECTED_FIELD = "unexpected_field"
    VALIDATION_FAILED = "validation_failed"


class SilverTransformationError(Exception):
    """Custom exception for silver transformation errors"""
    pass


class SilverTransformationService:
    """
    Service for transforming Bronze data into Silver layer with quality checks and quarantine
    """

    def __init__(self, storage_type: str = 'local'):
        """
        Initialize the Silver transformation service

        Args:
            storage_type: Type of storage to use ('local' or 's3')
        """
        self.config = Config()
        self.storage_factory = BronzeStorageFactory()
        self.storage = self.storage_factory.create_storage(storage_type)
        self.quality_checker = QualityChecker()

        # Create quarantine directory if it doesn't exist
        self.quarantine_base_path = "./quarantine_storage"
        os.makedirs(self.quarantine_base_path, exist_ok=True)

    def discover_bronze_records(self, data_type: str, date_str: str,
                              location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover and load all Bronze records for a given date and type

        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            location: Location identifier for weather data (optional)

        Returns:
            List of bronze records
        """
        logger.info(f"Discovering Bronze records for {data_type} on {date_str}")

        # For this implementation, we'll simulate discovering records
        # In a real implementation, this would scan the bronze storage for matching keys
        # Since we're in a local-only environment, we'll just return a placeholder
        return []

    def transform_and_validate_bronze_to_silver(self, data_type: str, date_str: str,
                                              location: Optional[str] = None) -> Dict[str, Any]:
        """
        Transform Bronze data to Silver layer with validation and quality checks

        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            location: Location identifier for weather data (optional)

        Returns:
            Dictionary with transformation results
        """
        logger.info(f"Transforming {data_type} data from Bronze to Silver for {date_str}")

        # Validate data type early to prevent processing unsupported types
        if data_type not in ['demand', 'weather', 'generation']:
            raise ValueError(f"Unsupported data type: {data_type}")

        try:
            # Step 1: Load raw Bronze data
            raw_data_list = self._load_bronze_data(data_type, date_str, location)
            if not raw_data_list:
                logger.warning(f"No Bronze data found for {data_type} on {date_str}")
                return {
                    'status': TransformationStatus.FAILURE.value,
                    'valid_records': [],
                    'quarantined_records': [],
                    'summary': {
                        'total_input_records': 0,
                        'valid_records': 0,
                        'quarantined_records': 0,
                        'duplicate_records': 0,
                        'missing_values': 0,
                        'invalid_values': 0,
                        'quality_score': 0.0,
                        'error_message': 'No input data found'
                    }
                }

            # Step 2: Transform and validate each record
            valid_records = []
            quarantined_records = []
            total_input_records = 0
            duplicate_count = 0
            missing_count = 0
            invalid_count = 0

            # Track unique records for duplicate detection
            seen_records = set()

            for raw_data in raw_data_list:
                # Extract metadata
                metadata = self._extract_metadata(raw_data)

                # Transform data based on type
                if data_type == 'demand':
                    transformed_data = self._transform_demand_to_silver(raw_data, metadata)
                elif data_type == 'weather':
                    transformed_data = self._transform_weather_to_silver(raw_data, metadata)
                elif data_type == 'generation':
                    transformed_data = self._transform_generation_to_silver(raw_data, metadata)
                else:
                    # Handle unknown data types by quarantining
                    quarantine_record = self._create_quarantine_record(
                        raw_data, metadata,
                        QuarantineReason.SCHEMA_VIOLATION.value,
                        f"Unknown data type: {data_type}"
                    )
                    quarantined_records.append(quarantine_record)
                    continue

                if transformed_data is None:
                    # Transform failed, quarantine the record
                    quarantine_record = self._create_quarantine_record(
                        raw_data, metadata,
                        QuarantineReason.VALIDATION_FAILED.value,
                        "Transformation failed"
                    )
                    quarantined_records.append(quarantine_record)
                    continue

                # Validate transformed data
                validation_result = self._validate_transformed_data(transformed_data, data_type)

                if validation_result['valid']:
                    # Check for duplicates
                    record_hash = self._generate_record_hash(transformed_data)

                    if record_hash in seen_records:
                        # Duplicate detected
                        duplicate_count += 1
                        quarantine_record = self._create_quarantine_record(
                            raw_data, metadata,
                            QuarantineReason.DUPLICATE_DETECTED.value,
                            "Duplicate record detected",
                            transformed_data
                        )
                        quarantined_records.append(quarantine_record)
                    else:
                        # Valid record
                        seen_records.add(record_hash)
                        # Add lineage metadata
                        transformed_data_with_lineage = self._add_lineage_metadata(
                            transformed_data, metadata, data_type
                        )
                        valid_records.append(transformed_data_with_lineage)
                        total_input_records += 1
                else:
                    # Invalid record, quarantine it
                    invalid_count += 1
                    quarantine_record = self._create_quarantine_record(
                        raw_data, metadata,
                        QuarantineReason.SCHEMA_VIOLATION.value,
                        f"Validation failed: {validation_result['errors']}",
                        transformed_data
                    )
                    quarantined_records.append(quarantine_record)
                    total_input_records += 1

            # Calculate quality score (simplified)
            if total_input_records > 0:
                quality_score = (len(valid_records) / total_input_records) * 100
            else:
                quality_score = 0.0

            # Step 3: Save valid records to Silver layer
            silver_saved = self._save_valid_records_to_silver(valid_records, data_type, date_str, location)

            # Step 4: Save quarantined records to quarantine storage
            quarantine_saved = self._save_quarantined_records_to_storage(quarantined_records, data_type, date_str, location)

            # Generate summary
            summary = {
                'total_input_records': total_input_records,
                'valid_records': len(valid_records),
                'quarantined_records': len(quarantined_records),
                'duplicate_records': duplicate_count,
                'missing_values': missing_count,
                'invalid_values': invalid_count,
                'quality_score': round(quality_score, 2),
                'silver_saved': silver_saved,
                'quarantine_saved': quarantine_saved,
                'transformation_timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Determine overall status
            if len(valid_records) > 0 and len(quarantined_records) == 0:
                status = TransformationStatus.SUCCESS.value
            elif len(valid_records) > 0 and len(quarantined_records) > 0:
                status = TransformationStatus.PARTIAL_SUCCESS.value
            else:
                status = TransformationStatus.FAILURE.value

            return {
                'status': status,
                'valid_records': valid_records,
                'quarantined_records': quarantined_records,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"Error in transformation pipeline: {str(e)}")
            return {
                'status': TransformationStatus.FAILURE.value,
                'valid_records': [],
                'quarantined_records': [],
                'summary': {
                    'total_input_records': 0,
                    'valid_records': 0,
                    'quarantined_records': 0,
                    'duplicate_records': 0,
                    'missing_values': 0,
                    'invalid_values': 0,
                    'quality_score': 0.0,
                    'error_message': str(e)
                }
            }

    def _load_bronze_data(self, data_type: str, date_str: str,
                          location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load raw data from Bronze storage

        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            location: Location identifier for weather data (optional)

        Returns:
            List of raw data records
        """
        # Validate supported data types
        if data_type not in ['demand', 'weather', 'generation']:
            logger.warning(f"Unsupported data type: {data_type}")
            return []

        try:
            # Create bronze storage instance
            bronze_storage = self.storage_factory.create_storage('s3')

            # For weather data, we need to handle location properly
            if data_type == 'weather' and location:
                # Try to get the weather data for the specific location
                raw_data = bronze_storage.get_raw_data(data_type, date_str, location)
                if raw_data:
                    return [raw_data]
                else:
                    logger.warning(f"No Bronze data found for {data_type} at location {location} on {date_str}")
                    return []
            else:
                # For demand and generation, we look for all data of that type on the date
                # In a real implementation, we would scan for all relevant keys, but for now
                # we'll attempt to get the data assuming it's stored with the standard key pattern

                # Since we don't have a way to discover all keys without knowing the exact ingestion IDs,
                # we'll try to load a few common patterns that might exist
                possible_keys = [
                    f"bronze/{data_type}/{date_str}",
                    f"bronze/{data_type}/{date_str}/",
                ]

                # For now, we'll try to load data with the standard approach
                # This would be enhanced with actual key discovery in a real implementation
                raw_data = bronze_storage.get_raw_data(data_type, date_str)
                if raw_data:
                    return [raw_data]
                else:
                    logger.warning(f"No Bronze data found for {data_type} on {date_str}")
                    return []

        except Exception as e:
            logger.error(f"Error loading Bronze data for {data_type}: {str(e)}")
            return []

    def _extract_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from raw data

        Args:
            raw_data: Raw data from Bronze layer

        Returns:
            Dictionary with metadata
        """
        metadata = {
            'source': raw_data.get('source', 'unknown'),
            'ingestion_id': raw_data.get('ingestion_id', 'unknown'),
            'timestamp': raw_data.get('timestamp', datetime.now(timezone.utc).isoformat()),
            'data_type': raw_data.get('data_type', 'unknown')
        }

        # Add location info for weather data
        if 'latitude' in raw_data and 'longitude' in raw_data:
            metadata['location'] = f"{raw_data['latitude']}_{raw_data['longitude']}"

        return metadata

    def _transform_demand_to_silver(self, raw_data: Dict[str, Any],
                                  metadata: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Transform EirGrid demand data to Silver layer format

        Args:
            raw_data: Raw EirGrid demand data
            metadata: Metadata from raw data

        Returns:
            List of transformed records or None if failed
        """
        try:
            transformed_records = []
            date_str = raw_data.get('date', '')

            # Validate demand values
            demand_values = raw_data.get('demand_values', [])
            if not isinstance(demand_values, list):
                return None

            for entry in demand_values:
                if not isinstance(entry, dict):
                    continue

                # Validate required fields
                if 'timestamp' not in entry or 'value' not in entry:
                    continue

                # Normalize timestamp
                try:
                    timestamp = pd.to_datetime(entry['timestamp']).tz_convert('UTC')
                except Exception:
                    # Skip invalid timestamps
                    continue

                # Validate numeric value
                try:
                    value = float(entry['value'])
                except (ValueError, TypeError):
                    # Skip invalid numeric values
                    continue

                # Create transformed record
                transformed_record = {
                    'date': date_str,
                    'timestamp': timestamp.isoformat(),
                    'value': value,
                    'source': metadata.get('source', 'unknown'),
                    'ingestion_id': metadata.get('ingestion_id', 'unknown'),
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }

                transformed_records.append(transformed_record)

            return transformed_records

        except Exception as e:
            logger.error(f"Error transforming demand data: {str(e)}")
            return None

    def _transform_weather_to_silver(self, raw_data: Dict[str, Any],
                                   metadata: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Transform Open-Meteo weather data to Silver layer format

        Args:
            raw_data: Raw Open-Meteo weather data
            metadata: Metadata from raw data

        Returns:
            List of transformed records or None if failed
        """
        try:
            transformed_records = []

            # Extract hourly data
            hourly_data = raw_data.get('hourly', {})
            timestamps = hourly_data.get('time', [])
            temperatures = hourly_data.get('temperature_2m', [])
            wind_speeds = hourly_data.get('wind_speed_10m', [])

            # Validate data consistency
            if len(timestamps) != len(temperatures) or len(timestamps) != len(wind_speeds):
                # This might be acceptable for partial data - we'll process what we have
                max_length = min(len(timestamps), len(temperatures), len(wind_speeds))
                timestamps = timestamps[:max_length]
                temperatures = temperatures[:max_length]
                wind_speeds = wind_speeds[:max_length]

            # Process each timestamp
            for i, timestamp_str in enumerate(timestamps):
                try:
                    timestamp = pd.to_datetime(timestamp_str).tz_convert('UTC')
                except Exception:
                    continue  # Skip invalid timestamps

                # Extract temperature (handle missing values)
                try:
                    temp = float(temperatures[i]) if i < len(temperatures) else None
                except (ValueError, TypeError):
                    temp = None

                # Extract wind speed (handle missing values)
                try:
                    wind_speed = float(wind_speeds[i]) if i < len(wind_speeds) else None
                except (ValueError, TypeError):
                    wind_speed = None

                # Create transformed record
                transformed_record = {
                    'latitude': raw_data.get('latitude'),
                    'longitude': raw_data.get('longitude'),
                    'timestamp': timestamp.isoformat(),
                    'temperature': temp,
                    'wind_speed': wind_speed,
                    'source': metadata.get('source', 'unknown'),
                    'ingestion_id': metadata.get('ingestion_id', 'unknown'),
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }

                transformed_records.append(transformed_record)

            return transformed_records

        except Exception as e:
            logger.error(f"Error transforming weather data: {str(e)}")
            return None

    def _transform_generation_to_silver(self, raw_data: Dict[str, Any],
                                      metadata: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Transform EirGrid generation data to Silver layer format

        Args:
            raw_data: Raw EirGrid generation data
            metadata: Metadata from raw data

        Returns:
            List of transformed records or None if failed
        """
        try:
            transformed_records = []
            date_str = raw_data.get('date', '')

            # Validate generation values
            generation_values = raw_data.get('generation_values', [])
            if not isinstance(generation_values, list):
                return None

            for entry in generation_values:
                if not isinstance(entry, dict):
                    continue

                # Validate required fields
                if 'timestamp' not in entry or 'value' not in entry or 'fuel_type' not in entry:
                    continue

                # Normalize timestamp
                try:
                    timestamp = pd.to_datetime(entry['timestamp']).tz_convert('UTC')
                except Exception:
                    continue  # Skip invalid timestamps

                # Validate numeric value
                try:
                    value = float(entry['value'])
                except (ValueError, TypeError):
                    continue  # Skip invalid numeric values

                # Validate fuel type
                fuel_type = entry.get('fuel_type', '').strip()
                if not fuel_type:
                    continue  # Skip invalid fuel types

                # Create transformed record
                transformed_record = {
                    'date': date_str,
                    'timestamp': timestamp.isoformat(),
                    'value': value,
                    'fuel_type': fuel_type,
                    'source': metadata.get('source', 'unknown'),
                    'ingestion_id': metadata.get('ingestion_id', 'unknown'),
                    'processed_at': datetime.now(timezone.utc).isoformat()
                }

                transformed_records.append(transformed_record)

            return transformed_records

        except Exception as e:
            logger.error(f"Error transforming generation data: {str(e)}")
            return None

    def _validate_transformed_data(self, transformed_data: List[Dict[str, Any]],
                                 data_type: str) -> Dict[str, Any]:
        """
        Validate transformed data according to Silver layer requirements

        Args:
            transformed_data: Transformed data records
            data_type: Type of data ('demand', 'weather', 'generation')

        Returns:
            Dictionary with validation results
        """
        try:
            # Basic validation - check if data is a list and not empty
            if not isinstance(transformed_data, list):
                return {'valid': False, 'errors': ['Transformed data must be a list']}

            if len(transformed_data) == 0:
                return {'valid': False, 'errors': ['No transformed data to validate']}

            # Validate each record based on data type
            errors = []
            for record in transformed_data:
                if not isinstance(record, dict):
                    errors.append('Each record must be a dictionary')
                    continue

                # Validate required fields for each data type
                if data_type == 'demand':
                    required_fields = ['date', 'timestamp', 'value']
                    for field in required_fields:
                        if field not in record:
                            errors.append(f'Missing required field: {field}')

                elif data_type == 'weather':
                    required_fields = ['latitude', 'longitude', 'timestamp', 'temperature']
                    for field in required_fields:
                        if field not in record:
                            errors.append(f'Missing required field: {field}')

                elif data_type == 'generation':
                    required_fields = ['date', 'timestamp', 'value', 'fuel_type']
                    for field in required_fields:
                        if field not in record:
                            errors.append(f'Missing required field: {field}')

            return {
                'valid': len(errors) == 0,
                'errors': errors
            }

        except Exception as e:
            return {'valid': False, 'errors': [f'Validation error: {str(e)}']}

    def _generate_record_hash(self, record: Dict[str, Any]) -> str:
        """
        Generate a hash for a record to detect duplicates

        Args:
            record: Record dictionary

        Returns:
            Hash string of the record
        """
        # Create a stable representation of the record
        record_copy = record.copy()
        # Remove timestamp and processed_at fields for comparison
        if 'timestamp' in record_copy:
            record_copy.pop('timestamp')
        if 'processed_at' in record_copy:
            record_copy.pop('processed_at')

        # Sort keys for consistent hashing
        sorted_items = sorted(record_copy.items())
        record_str = json.dumps(sorted_items, sort_keys=True, separators=(',', ':'))

        return hashlib.md5(record_str.encode()).hexdigest()

    def _add_lineage_metadata(self, record: Dict[str, Any], metadata: Dict[str, Any],
                            data_type: str) -> Dict[str, Any]:
        """
        Add lineage metadata to a record

        Args:
            record: Record to enhance with metadata
            metadata: Original metadata
            data_type: Type of data

        Returns:
            Record with lineage metadata
        """
        lineage_metadata = {
            'source': metadata.get('source'),
            'dataset': data_type,
            'bronze_ingestion_id': metadata.get('ingestion_id'),
            'bronze_timestamp': metadata.get('timestamp'),
            'silver_transformation_version': '1.0',
            'silver_transformation_timestamp': datetime.now(timezone.utc).isoformat(),
            'silver_validation_status': 'valid'
        }

        # Merge with existing record
        enhanced_record = record.copy()
        enhanced_record.update(lineage_metadata)

        return enhanced_record

    def _create_quarantine_record(self, raw_data: Dict[str, Any], metadata: Dict[str, Any],
                                reason: str, error_msg: str,
                                transformed_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a quarantine record with all relevant information

        Args:
            raw_data: Original raw data
            metadata: Metadata from raw data
            reason: Reason for quarantine
            error_msg: Error message
            transformed_data: Transformed data (if available)

        Returns:
            Quarantine record dictionary
        """
        quarantine_record = {
            'quarantine_reason': reason,
            'error_message': error_msg,
            'original_bronze_source': metadata.get('source'),
            'original_bronze_dataset': metadata.get('data_type'),
            'original_bronze_ingestion_id': metadata.get('ingestion_id'),
            'original_bronze_timestamp': metadata.get('timestamp'),
            'quarantine_timestamp': datetime.now(timezone.utc).isoformat(),
            'quarantine_id': str(uuid.uuid4()),
            'original_payload': raw_data,
            'transformed_data': transformed_data,
            'location': metadata.get('location', 'unknown')
        }

        return quarantine_record

    def _save_valid_records_to_silver(self, valid_records: List[Dict[str, Any]],
                                    data_type: str, date_str: str,
                                    location: Optional[str] = None) -> bool:
        """
        Save valid records to Silver storage (simulated in local environment)

        Args:
            valid_records: List of valid records
            data_type: Type of data
            date_str: Date string
            location: Location for weather data

        Returns:
            True if successful, False otherwise
        """
        try:
            # For local environment, we'll save to a simulated Silver storage
            # In a real implementation, this would write to actual S3 or filesystem

            # Create a simple JSON file structure for demonstration
            silver_dir = f"./silver_storage/{data_type}"
            if location:
                silver_dir = f"{silver_dir}/{location}"

            os.makedirs(silver_dir, exist_ok=True)

            # Save as JSON files for each date
            silver_file = f"{silver_dir}/{date_str}.json"
            with open(silver_file, 'w') as f:
                json.dump(valid_records, f, indent=2)

            logger.info(f"Saved {len(valid_records)} valid records to Silver storage at {silver_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving valid records to Silver: {str(e)}")
            return False

    def _save_quarantined_records_to_storage(self, quarantined_records: List[Dict[str, Any]],
                                           data_type: str, date_str: str,
                                           location: Optional[str] = None) -> bool:
        """
        Save quarantined records to quarantine storage (simulated in local environment)

        Args:
            quarantined_records: List of quarantined records
            data_type: Type of data
            date_str: Date string
            location: Location for weather data

        Returns:
            True if successful, False otherwise
        """
        try:
            # For local environment, we'll save to a simulated quarantine storage
            if not quarantined_records:
                return True

            quarantine_dir = f"./quarantine_storage/{data_type}"
            if location:
                quarantine_dir = f"{quarantine_dir}/{location}"

            os.makedirs(quarantine_dir, exist_ok=True)

            # Save as JSON files for each date
            quarantine_file = f"{quarantine_dir}/{date_str}_quarantined.json"
            with open(quarantine_file, 'w') as f:
                json.dump(quarantined_records, f, indent=2)

            logger.info(f"Saved {len(quarantined_records)} quarantined records to quarantine storage at {quarantine_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving quarantined records to storage: {str(e)}")
            return False

    def get_transformation_summary(self, data_type: str, date_str: str,
                                 location: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of transformation results for a given date and type

        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            location: Location identifier for weather data (optional)

        Returns:
            Dictionary with transformation summary
        """
        # This is a simplified implementation for local environment
        # In a real implementation, this would read from the actual storage systems
        return {
            'data_type': data_type,
            'date': date_str,
            'location': location,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'bronze_processed': True,
            'silver_processed': True,
            'quarantine_processed': True
        }


def main():
    """Main function to demonstrate the transformation service"""
    logger.info("Starting Silver Transformation Service demo")

    # Initialize transformation service
    transformer = SilverTransformationService('local')

    # Transform demand data
    logger.info("Transforming demand data...")
    result = transformer.transform_and_validate_bronze_to_silver('demand', '2023-01-01')

    print("Demand Transformation Result:")
    print(f"Status: {result['status']}")
    print(f"Valid Records: {result['summary']['valid_records']}")
    print(f"Quarantined Records: {result['summary']['quarantined_records']}")
    print(f"Quality Score: {result['summary']['quality_score']}%")

    # Transform weather data
    logger.info("Transforming weather data...")
    result = transformer.transform_and_validate_bronze_to_silver('weather', '2023-01-01')

    print("\nWeather Transformation Result:")
    print(f"Status: {result['status']}")
    print(f"Valid Records: {result['summary']['valid_records']}")
    print(f"Quarantined Records: {result['summary']['quarantined_records']}")
    print(f"Quality Score: {result['summary']['quality_score']}%")

    # Transform generation data
    logger.info("Transforming generation data...")
    result = transformer.transform_and_validate_bronze_to_silver('generation', '2023-01-01')

    print("\nGeneration Transformation Result:")
    print(f"Status: {result['status']}")
    print(f"Valid Records: {result['summary']['valid_records']}")
    print(f"Quarantined Records: {result['summary']['quarantined_records']}")
    print(f"Quality Score: {result['summary']['quality_score']}%")


if __name__ == "__main__":
    main()