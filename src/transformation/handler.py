"""
Lambda handler for transformation functions
"""
import json
from datetime import datetime, timedelta
from loguru import logger
from src.transformation.data_transformation import DataTransformer
from src.transformation.bronze_layer import BronzeLayerProcessor


# Module-level instances for testing compatibility
_data_transformer = DataTransformer()
_bronze_layer_processor = BronzeLayerProcessor()


def lambda_handler(event, context):
    """
    Main Lambda handler for data transformation pipeline
    
    Args:
        event (dict): Event data passed to Lambda
        context (object): Lambda context object
        
    Returns:
        dict: Response with status and result
    """
    logger.info("Starting transformation Lambda function")
    
    try:
        # Handle EventBridge event envelope or direct invocation
        data_type = None
        date_str = None
        raw_data = None
        
        # Check if this is an EventBridge event (contains 'detail' field)
        if 'detail' in event:
            # EventBridge event structure
            detail = event.get('detail', {})
            data_type = detail.get('data_type')
            
            # Parse date range for EirGrid and Open-Meteo events
            if data_type == 'eirgrid':
                # EirGrid events have date_range
                date_range = detail.get('date_range')
                if not date_range:
                    raise ValueError("Missing date_range in EirGrid event")
                
                # Parse date range
                start_date_str, end_date_str = date_range.split(' to ')
                
                # Process EirGrid data (both demand and generation)
                success_results = []
                
                # First process demand data
                demand_results = process_eirgrid_data(detail, 'demand', start_date_str, end_date_str)
                success_results.extend(demand_results)
                
                # Then process generation data
                generation_results = process_eirgrid_data(detail, 'generation', start_date_str, end_date_str)
                success_results.extend(generation_results)
                
                # Return success if all operations succeeded
                if all(success_results):
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'status': 'success',
                            'message': 'EirGrid data processed successfully',
                            'results': success_results
                        })
                    }
                else:
                    return {
                        'statusCode': 500,
                        'body': json.dumps({
                            'status': 'partial_failure',
                            'message': 'Some EirGrid data processing failed',
                            'results': success_results
                        })
                    }
            
            elif data_type == 'openmeteo':
                # Open-Meteo events have location and date_range
                location = detail.get('location')
                if not location:
                    raise ValueError("Missing location in Open-Meteo event")
                
                date_range = detail.get('date_range')
                if not date_range:
                    raise ValueError("Missing date_range in Open-Meteo event")
                
                # Parse date range
                start_date_str, end_date_str = date_range.split(' to ')
                
                # Process Open-Meteo data
                success_results = process_openmeteo_data(detail, location, start_date_str, end_date_str)
                
                # Return success if all operations succeeded
                if all(success_results):
                    return {
                        'statusCode': 200,
                        'body': json.dumps({
                            'status': 'success',
                            'message': 'Open-Meteo data processed successfully',
                            'results': success_results
                        })
                    }
                else:
                    return {
                        'statusCode': 500,
                        'body': json.dumps({
                            'status': 'partial_failure',
                            'message': 'Some Open-Meteo data processing failed',
                            'results': success_results
                        })
                    }
            
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        
        else:
            # Direct invocation - expects data_type, date_str, and raw_data
            data_type = event.get('data_type')
            date_str = event.get('date_str')
            raw_data = event.get('raw_data')
            
            if not all([data_type, date_str, raw_data]):
                raise ValueError("Missing required fields for direct invocation")
            
            # Process direct invocation
            success = _data_transformer.process_incremental_data(data_type, date_str, raw_data)
            
            if success:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'message': 'Direct data processing successful'
                    })
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'status': 'failure',
                        'message': 'Direct data processing failed'
                    })
                }
        
        # Default return (shouldn't reach here)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'message': 'No data processed'
            })
        }
    
    except Exception as e:
        # Re-raise AWS service errors to allow them to propagate for testing
        # but keep other exceptions wrapped in response for production safety
        from botocore.exceptions import ClientError
        if isinstance(e, ClientError):
            raise  # Propagate AWS service errors for testing purposes
        
        logger.error(f"Error in transformation Lambda: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Transformation failed: {str(e)}',
                'status': 'error'
            })
        }


def process_eirgrid_data(detail, data_subtype, start_date_str, end_date_str):
    """Process EirGrid data for a range of dates."""
    from datetime import datetime, timedelta
    
    success_results = []
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Generate all dates in the range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        data_type = data_subtype
        
        # For EirGrid data, we need to retrieve the raw data from Bronze layer
        # Use the module-level instance for testing compatibility
        bronze_files = _bronze_layer_processor.list_timestamped_ingestion_objects(data_type, date_str)
        
        raw_data = None
        if bronze_files:
            # Get the most recent file (using LastModified instead of lexicographic sort)
            latest_file = max(bronze_files, key=lambda f: f['LastModified'])
            raw_data = _bronze_layer_processor.retrieve_bronze_data(latest_file['Key'])
        
        # Process the data pipeline
        if raw_data is not None:
            # Use the module-level instance for testing compatibility
            success = _data_transformer.process_incremental_data(data_type, date_str, raw_data)
            success_results.append(success)
        else:
            # If no data found, we consider it a failure
            success_results.append(False)
        
        current_date += timedelta(days=1)
    
    return success_results


def process_openmeteo_data(detail, location, start_date_str, end_date_str):
    """Process Open-Meteo weather data for a range of dates."""
    from datetime import datetime, timedelta
    
    success_results = []
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Generate all dates in the range
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        data_type = 'weather'
        
        # For Open-Meteo data, we need to retrieve the raw data from Bronze layer
        # Construct the correct prefix for weather data with location
        weather_prefix = f"weather/{location}/{date_str}/"
        # Use the module-level instance for testing compatibility
        bronze_files = _bronze_layer_processor.list_timestamped_ingestion_objects('weather', date_str, weather_prefix)
        
        raw_data = None
        if bronze_files:
            # Get the most recent file (using LastModified instead of lexicographic sort)
            latest_file = max(bronze_files, key=lambda f: f['LastModified'])
            raw_data = _bronze_layer_processor.retrieve_bronze_data(latest_file['Key'])
        
        # Process the data pipeline
        if raw_data is not None:
            # Use the module-level instance for testing compatibility
            success = _data_transformer.process_incremental_data(data_type, date_str, raw_data)
            success_results.append(success)
        else:
            # If no data found, we consider it a failure
            success_results.append(False)
        
        current_date += timedelta(days=1)
    
    return success_results