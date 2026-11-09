#!/usr/bin/env python3
"""
AWS Lambda handlers for Silver and Gold transformations
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
import boto3
from botocore.exceptions import ClientError

from src.transformation.silver_transformation import SilverTransformationService
from src.transformation.gold_transformation import GoldTransformationService
from src.storage.bronze_storage import BronzeStorageFactory
from src.common.config import Config


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for transformation pipeline

    Args:
        event: Lambda event data
        context: Lambda context

    Returns:
        Dictionary with transformation results
    """
    logger.info("Starting transformation Lambda function")

    try:
        # Determine transformation type from event
        transformation_type = event.get('transformation_type')

        if transformation_type == 'silver':
            return transform_silver_handler(event, context)
        elif transformation_type == 'gold':
            return transform_gold_handler(event, context)
        else:
            raise ValueError(f"Unsupported transformation type: {transformation_type}")

    except Exception as e:
        logger.error(f"Error in transformation Lambda: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Transformation failed: {str(e)}',
                'status': 'error'
            })
        }


def transform_silver_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Transform Bronze data to Silver layer

    Expected event structure:
    {
        "transformation_type": "silver",
        "data_type": "demand|weather|generation",
        "date": "YYYY-MM-DD",
        "location": "optional-location",
        "execution_id": "unique-id"
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "status": "success|failure",
            "execution_id": "uuid",
            "dataset": "demand|weather|generation",
            "source": "eirgrid|openmeteo",
            "status": "success|partial_success|failure",
            "input_bucket": "bronze-bucket-name",
            "input_keys": ["list-of-input-keys"],
            "output_bucket": "silver-bucket-name",
            "output_keys": ["list-of-output-keys"],
            "records_read": 10,
            "records_written": 8,
            "records_quarantined": 2,
            "quality_score": 95.5,
            "started_at": "2023-01-01T10:00:00Z",
            "completed_at": "2023-01-01T10:05:00Z"
        }
    }
    """
    logger.info("Starting Silver transformation")

    # Parse event parameters
    data_type = event.get('data_type')
    date_str = event.get('date')
    location = event.get('location')
    execution_id = event.get('execution_id')

    if not all([data_type, date_str]):
        raise ValueError("Missing required parameters: data_type and date")

    # Initialize services
    silver_service = SilverTransformationService(storage_type='s3')

    # Track execution metadata
    started_at = datetime.utcnow().isoformat()

    try:
        # Perform transformation
        result = silver_service.transform_and_validate_bronze_to_silver(
            data_type=data_type,
            date_str=date_str,
            location=location
        )

        completed_at = datetime.utcnow().isoformat()

        # Prepare response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'execution_id': execution_id,
                'dataset': data_type,
                'source': 'eirgrid' if data_type in ['demand', 'generation'] else 'openmeteo',
                'status': result.get('status', 'success'),
                'input_bucket': silver_service.config.BRONZE_BUCKET,
                'input_keys': result.get('input_keys', []),
                'output_bucket': silver_service.config.SILVER_BUCKET,
                'output_keys': result.get('output_keys', []),
                'records_read': result.get('records_read', 0),
                'records_written': result.get('records_written', 0),
                'records_quarantined': result.get('records_quarantined', 0),
                'quality_score': result.get('quality_score', 0.0),
                'started_at': started_at,
                'completed_at': completed_at
            })
        }

        return response

    except Exception as e:
        logger.error(f"Silver transformation failed: {e}")
        completed_at = datetime.utcnow().isoformat()

        # Raise exception instead of returning 500 status code
        # This will cause Step Functions to treat it as a task failure
        raise Exception(f"Silver transformation failed: {str(e)}")


def transform_gold_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Transform Silver data to Gold layer

    Expected event structure:
    {
        "transformation_type": "gold",
        "data_type": "demand|weather|generation",
        "date": "YYYY-MM-DD",
        "execution_id": "unique-id"
    }

    Returns:
    {
        "statusCode": 200,
        "body": {
            "status": "success|failure",
            "execution_id": "uuid",
            "dataset": "demand|weather|generation",
            "status": "success|partial_success|failure",
            "input_bucket": "silver-bucket-name",
            "input_keys": ["list-of-input-keys"],
            "output_bucket": "gold-bucket-name",
            "output_keys": ["list-of-output-keys"],
            "records_read": 10,
            "records_written": 8,
            "quality_score": 95.5,
            "started_at": "2023-01-01T10:00:00Z",
            "completed_at": "2023-01-01T10:05:00Z"
        }
    }
    """
    logger.info("Starting Gold transformation")

    # Parse event parameters
    data_type = event.get('data_type')
    date_str = event.get('date')
    execution_id = event.get('execution_id')

    if not all([data_type, date_str]):
        raise ValueError("Missing required parameters: data_type and date")

    # Initialize services
    gold_service = GoldTransformationService(storage_type='s3')

    # Track execution metadata
    started_at = datetime.utcnow().isoformat()

    try:
        # Perform transformation
        result = gold_service.transform_and_validate_silver_to_gold(
            data_type=data_type,
            date_str=date_str
        )

        completed_at = datetime.utcnow().isoformat()

        # Prepare response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'execution_id': execution_id,
                'dataset': data_type,
                'status': result.get('status', 'success'),
                'input_bucket': gold_service.config.SILVER_BUCKET,
                'input_keys': result.get('input_keys', []),
                'output_bucket': gold_service.config.GOLD_BUCKET,
                'output_keys': result.get('output_keys', []),
                'records_read': result.get('records_read', 0),
                'records_written': result.get('records_written', 0),
                'quality_score': result.get('quality_score', 0.0),
                'started_at': started_at,
                'completed_at': completed_at
            })
        }

        return response

    except Exception as e:
        logger.error(f"Gold transformation failed: {e}")
        completed_at = datetime.utcnow().isoformat()

        # Raise exception instead of returning 500 status code
        # This will cause Step Functions to treat it as a task failure
        raise Exception(f"Gold transformation failed: {str(e)}")


# Test helper functions for local testing
def test_silver_transformation():
    """Test Silver transformation with mocked data"""
    print("Testing Silver transformation...")

    # Mock event
    event = {
        'transformation_type': 'silver',
        'data_type': 'weather',
        'date': '2023-01-01',
        'location': 'dublin',
        'execution_id': 'test-execution-123'
    }

    # Mock context
    context = type('obj', (object,), {'function_name': 'TestSilverFunction'})()

    # This would normally be run in AWS Lambda environment
    # For testing purposes, we just verify the function exists
    assert callable(transform_silver_handler)
    print("✓ Silver transformation handler exists")


def test_gold_transformation():
    """Test Gold transformation with mocked data"""
    print("Testing Gold transformation...")

    # Mock event
    event = {
        'transformation_type': 'gold',
        'data_type': 'weather',
        'date': '2023-01-01',
        'execution_id': 'test-execution-456'
    }

    # Mock context
    context = type('obj', (object,), {'function_name': 'TestGoldFunction'})()

    # This would normally be run in AWS Lambda environment
    # For testing purposes, we just verify the function exists
    assert callable(transform_gold_handler)
    print("✓ Gold transformation handler exists")


if __name__ == "__main__":
    test_silver_transformation()
    test_gold_transformation()
    print("All tests passed!")