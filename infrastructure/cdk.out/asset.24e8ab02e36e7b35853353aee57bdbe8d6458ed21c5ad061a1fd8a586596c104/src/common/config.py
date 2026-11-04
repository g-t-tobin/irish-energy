"""Configuration management for Irish Energy Analytics Platform"""

import os
from typing import Optional

class Config:
    """Configuration class for the platform"""
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'irish-energy-data-platform-dev')
    
    # S3 Bucket Names
    BRONZE_BUCKET = os.getenv('BRONZE_BUCKET', 'irish-energy-bronze-default')
    SILVER_BUCKET = os.getenv('SILVER_BUCKET', 'irish-energy-silver-default')
    GOLD_BUCKET = os.getenv('GOLD_BUCKET', 'irish-energy-gold-default')
    
    # Data Sources
    EIRGRID_API_URL = os.getenv('EIRGRID_API_URL', 'https://api.eirgrid.com')
    OPEN_METEO_API_URL = os.getenv('OPEN_METEO_API_URL', 'https://archive-api.open-meteo.com')
    
    # Ingestion Settings
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    
    # Data Processing
    PARQUET_COMPRESSION = os.getenv('PARQUET_COMPRESSION', 'snappy')
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration values"""
        required_vars = [
            'BRONZE_BUCKET',
            'SILVER_BUCKET', 
            'GOLD_BUCKET',
            'EIRGRID_API_URL',
            'OPEN_METEO_API_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required configuration variables: {missing_vars}")
        
        return True