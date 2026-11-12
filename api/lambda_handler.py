import json
import sys
import os

# For Lambda execution, make sure we can import from the current directory
# The asset packaging puts everything in the root, so we need to adjust the import path
# Add the api directory to the Python path to ensure imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from main.py
from main import app

# Import mangum for Lambda integration
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    # Fallback for when mangum is not available
    def handler(event, context):
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Mangum not installed'})
        }