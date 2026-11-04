"""Common utility functions for Irish Energy Analytics Platform"""

import logging
from datetime import datetime
from typing import Optional

# Configure logging
def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Setup structured logging for the application"""
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    # Create console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()

def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate that start date is before end date"""
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        return start <= end
    except ValueError:
        return False