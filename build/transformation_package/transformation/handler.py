"""
Lambda handler for transformation functions
"""
import json
from loguru import logger
from src.transformation.data_transformation import DataTransformer


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
        # Parse the event
        data_type = event.get('data_type')
        date_str = event.get('date_str')
        raw_data = event.get('raw_data')
        
        if not data_type or not date_str:
            raise ValueError("Missing required parameters: data_type and date_str")
            
        # Initialize transformer
        transformer = DataTransformer()
        
        # Process the data pipeline
        success = transformer.process_incremental_data(data_type, date_str, raw_data)
        
        if success:
            logger.info(f"Successfully processed {data_type} data for {date_str}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully transformed {data_type} data for {date_str}',
                    'data_type': data_type,
                    'date': date_str,
                    'status': 'success'
                })
            }
        else:
            logger.error(f"Failed to transform {data_type} data for {date_str}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'Failed to transform {data_type} data for {date_str}',
                    'data_type': data_type,
                    'date': date_str,
                    'status': 'failed'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in transformation Lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Transformation failed: {str(e)}',
                'status': 'error'
            })
        }