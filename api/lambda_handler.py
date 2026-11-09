import json
import sys
import os

# For Lambda execution, make sure we can import from the current directory
# The asset packaging puts everything in the root, so we don't need to manipulate sys.path
# We can directly import from the local directory

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