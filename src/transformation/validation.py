"""
Validation utilities for data layers
"""
import boto3
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger
from src.common.config import Config
from src.transformation.bronze_layer import BronzeLayerProcessor
from src.transformation.silver_layer import SilverLayerProcessor
from src.transformation.gold_layer import GoldLayerProcessor

class LayerValidator:
    """
    Validates data at different layers of the data lake
    """

    def __init__(self):
        self.config = Config()
        self.s3_client = boto3.client('s3')
        self.bronze_processor = BronzeLayerProcessor()
        self.silver_processor = SilverLayerProcessor()
        self.gold_processor = GoldLayerProcessor()

    def validate_bronze_layer(self, data_type: str, date_str: str) -> Dict[str, Any]:
        """
        Validate Bronze layer data

        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Dict with validation results
        """
        try:
            # Check if Bronze object exists
            bronze_key = f"{data_type}/bronze/{date_str}.json"

            # Check if object exists in S3
            try:
                response = self.s3_client.head_object(
                    Bucket=self.config.BRONZE_BUCKET,
                    Key=bronze_key
                )

                # Check that object is not empty
                if response.get('ContentLength', 0) == 0:
                    logger.warning(f"Bronze object is empty: {bronze_key}")
                    return {
                        'valid': False,
                        'message': f"Bronze object is empty: {bronze_key}",
                        'errors': ['Object is empty']
                    }

            except Exception as e:
                if 'NoSuchKey' in str(e):
                    logger.warning(f"Bronze object not found: {bronze_key}")
                    return {
                        'valid': False,
                        'message': f"Bronze object not found: {bronze_key}",
                        'errors': ['Object not found']
                    }
                else:
                    logger.error(f"Error checking Bronze object: {str(e)}")
                    return {
                        'valid': False,
                        'message': f"Error checking Bronze object: {str(e)}",
                        'errors': [f'AWS error: {str(e)}']
                    }

            # Try to retrieve and parse the data
            try:
                raw_data = self.bronze_processor.retrieve_bronze_data(bronze_key)
                if raw_data is None:
                    logger.warning(f"Could not retrieve data from Bronze: {bronze_key}")
                    return {
                        'valid': False,
                        'message': f"Could not retrieve data from Bronze: {bronze_key}",
                        'errors': ['Could not retrieve data']
                    }

                # Validate data structure based on data type
                if data_type == 'demand':
                    if 'date' not in raw_data or 'demand_values' not in raw_data:
                        logger.warning(f"Invalid demand data structure: {bronze_key}")
                        return {
                            'valid': False,
                            'message': f"Invalid demand data structure: {bronze_key}",
                            'errors': ['Invalid demand data structure']
                        }

                elif data_type == 'weather':
                    if 'latitude' not in raw_data or 'longitude' not in raw_data:
                        logger.warning(f"Invalid weather data structure: {bronze_key}")
                        return {
                            'valid': False,
                            'message': f"Invalid weather data structure: {bronze_key}",
                            'errors': ['Invalid weather data structure']
                        }

                elif data_type == 'generation':
                    if 'date' not in raw_data or 'generation_values' not in raw_data:
                        logger.warning(f"Invalid generation data structure: {bronze_key}")
                        return {
                            'valid': False,
                            'message': f"Invalid generation data structure: {bronze_key}",
                            'errors': ['Invalid generation data structure']
                        }

            except Exception as e:
                logger.error(f"Error validating Bronze data: {str(e)}")
                return {
                    'valid': False,
                    'message': f"Error validating Bronze data: {str(e)}",
                    'errors': [f'Data validation error: {str(e)}']
                }

            logger.info(f"Bronze layer validation passed for {data_type} on {date_str}")
            return {
                'valid': True,
                'message': f"Bronze layer validation passed for {data_type} on {date_str}",
                'errors': []
            }

        except Exception as e:
            logger.error(f"Unexpected error in Bronze validation: {str(e)}")
            return {
                'valid': False,
                'message': f"Unexpected error in Bronze validation: {str(e)}",
                'errors': [f'Unexpected error: {str(e)}']
            }

    def validate_silver_layer(self, data_type: str, date_str: str) -> Dict[str, Any]:
        """
        Validate Silver layer data

        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Dict with validation results
        """
        try:
            # Check if Silver object exists
            silver_key = f"{data_type}/silver/{date_str}.parquet"

            # Check if object exists in S3
            try:
                response = self.s3_client.head_object(
                    Bucket=self.config.SILVER_BUCKET,
                    Key=silver_key
                )

                # Check that object is not empty
                if response.get('ContentLength', 0) == 0:
                    logger.warning(f"Silver object is empty: {silver_key}")
                    return {
                        'valid': False,
                        'message': f"Silver object is empty: {silver_key}",
                        'errors': ['Object is empty']
                    }

            except Exception as e:
                if 'NoSuchKey' in str(e):
                    logger.warning(f"Silver object not found: {silver_key}")
                    return {
                        'valid': False,
                        'message': f"Silver object not found: {silver_key}",
                        'errors': ['Object not found']
                    }
                else:
                    logger.error(f"Error checking Silver object: {str(e)}")
                    return {
                        'valid': False,
                        'message': f"Error checking Silver object: {str(e)}",
                        'errors': [f'AWS error: {str(e)}']
                    }

            # Try to read and parse the parquet file
            try:
                silver_df = self.silver_processor.retrieve_silver_data(silver_key)
                if silver_df is None or silver_df.empty:
                    logger.warning(f"Could not retrieve or parse Silver data: {silver_key}")
                    return {
                        'valid': False,
                        'message': f"Could not retrieve or parse Silver data: {silver_key}",
                        'errors': ['Could not retrieve or parse data']
                    }

                # Basic validation - check that we have some data
                if len(silver_df) == 0:
                    logger.warning(f"Silver data is empty: {silver_key}")
                    return {
                        'valid': False,
                        'message': f"Silver data is empty: {silver_key}",
                        'errors': ['Data is empty']
                    }

            except Exception as e:
                logger.error(f"Error validating Silver data: {str(e)}")
                return {
                    'valid': False,
                    'message': f"Error validating Silver data: {str(e)}",
                    'errors': [f'Data validation error: {str(e)}']
                }

            logger.info(f"Silver layer validation passed for {data_type} on {date_str}")
            return {
                'valid': True,
                'message': f"Silver layer validation passed for {data_type} on {date_str}",
                'errors': []
            }

        except Exception as e:
            logger.error(f"Unexpected error in Silver validation: {str(e)}")
            return {
                'valid': False,
                'message': f"Unexpected error in Silver validation: {str(e)}",
                'errors': [f'Unexpected error: {str(e)}']
            }

    def validate_gold_layer(self, data_type: str, date_str: str) -> Dict[str, Any]:
        """
        Validate Gold layer data

        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Dict with validation results
        """
        try:
            # Check if Gold object exists (partitioned by date)
            gold_key = f"{data_type}/gold/{date_str}.parquet"

            # Check if object exists in S3
            try:
                response = self.s3_client.head_object(
                    Bucket=self.config.GOLD_BUCKET,
                    Key=gold_key
                )

                # Check that object is not empty
                if response.get('ContentLength', 0) == 0:
                    logger.warning(f"Gold object is empty: {gold_key}")
                    return {
                        'valid': False,
                        'message': f"Gold object is empty: {gold_key}",
                        'errors': ['Object is empty']
                    }

            except Exception as e:
                if 'NoSuchKey' in str(e):
                    logger.warning(f"Gold object not found: {gold_key}")
                    return {
                        'valid': False,
                        'message': f"Gold object not found: {gold_key}",
                        'errors': ['Object not found']
                    }
                else:
                    logger.error(f"Error checking Gold object: {str(e)}")
                    return {
                        'valid': False,
                        'message': f"Error checking Gold object: {str(e)}",
                        'errors': [f'AWS error: {str(e)}']
                    }

            # Try to read and parse the parquet file
            try:
                gold_df = self.gold_processor.retrieve_gold_data(gold_key)
                if gold_df is None or gold_df.empty:
                    logger.warning(f"Could not retrieve or parse Gold data: {gold_key}")
                    return {
                        'valid': False,
                        'message': f"Could not retrieve or parse Gold data: {gold_key}",
                        'errors': ['Could not retrieve or parse data']
                    }

                # Basic validation - check that we have some data
                if len(gold_df) == 0:
                    logger.warning(f"Gold data is empty: {gold_key}")
                    return {
                        'valid': False,
                        'message': f"Gold data is empty: {gold_key}",
                        'errors': ['Data is empty']
                    }

            except Exception as e:
                logger.error(f"Error validating Gold data: {str(e)}")
                return {
                    'valid': False,
                    'message': f"Error validating Gold data: {str(e)}",
                    'errors': [f'Data validation error: {str(e)}']
                }

            logger.info(f"Gold layer validation passed for {data_type} on {date_str}")
            return {
                'valid': True,
                'message': f"Gold layer validation passed for {data_type} on {date_str}",
                'errors': []
            }

        except Exception as e:
            logger.error(f"Unexpected error in Gold validation: {str(e)}")
            return {
                'valid': False,
                'message': f"Unexpected error in Gold validation: {str(e)}",
                'errors': [f'Unexpected error: {str(e)}']
            }