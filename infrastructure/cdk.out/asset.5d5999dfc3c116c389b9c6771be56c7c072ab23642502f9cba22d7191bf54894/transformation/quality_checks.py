"""
Quality checks for data transformation processes
"""

from typing import Dict, Any, List, Tuple
import pandas as pd
import json
from datetime import datetime
from loguru import logger
from src.common.config import Config


class QualityChecker:
    """
    Performs data quality checks on Bronze, Silver, and Gold layer data
    """

    def __init__(self):
        self.config = Config()

    def validate_bronze_data(self, data: Dict[str, Any], data_type: str) -> bool:
        """
        Validate Bronze layer data
        
        Args:
            data: Raw data from ingestion
            data_type: Type of data ('demand', 'weather', 'generation')
            
        Returns:
            bool: True if data passes validation, False otherwise
        """
        logger.info(f"Validating {data_type} data at Bronze layer")
        
        try:
            if data_type == 'demand':
                return self._validate_demand_bronze(data)
            elif data_type == 'weather':
                return self._validate_weather_bronze(data)
            elif data_type == 'generation':
                return self._validate_generation_bronze(data)
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return False
                
        except Exception as e:
            logger.error(f"Validation error for {data_type}: {str(e)}")
            return False

    def _validate_demand_bronze(self, data: Dict[str, Any]) -> bool:
        """Validate demand data at Bronze layer"""
        required_fields = ['date', 'demand_values']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Validate date format
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            logger.error("Invalid date format in demand data")
            return False
            
        # Validate demand values
        if not isinstance(data['demand_values'], list):
            logger.error("Demand values must be a list")
            return False
            
        # Validate individual demand entries
        for entry in data['demand_values']:
            if not isinstance(entry, dict):
                logger.error("Each demand entry must be a dictionary")
                return False
                
            required_entry_fields = ['timestamp', 'value']
            for field in required_entry_fields:
                if field not in entry:
                    logger.error(f"Missing required entry field: {field}")
                    return False
                    
            # Validate timestamp format
            try:
                datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                logger.error("Invalid timestamp format in demand data")
                return False
                
            # Validate value is numeric
            if not isinstance(entry['value'], (int, float)):
                logger.error("Demand value must be numeric")
                return False
                
        return True

    def _validate_weather_bronze(self, data: Dict[str, Any]) -> bool:
        """Validate weather data at Bronze layer"""
        required_fields = ['latitude', 'longitude', 'hourly', 'daily']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Validate coordinates
        if not isinstance(data['latitude'], (int, float)) or \
           not isinstance(data['longitude'], (int, float)):
            logger.error("Latitude and longitude must be numeric")
            return False
            
        # Validate hourly data structure
        if not isinstance(data['hourly'], dict):
            logger.error("Hourly data must be a dictionary")
            return False
            
        # Validate daily data structure
        if not isinstance(data['daily'], dict):
            logger.error("Daily data must be a dictionary")
            return False
            
        return True

    def _validate_generation_bronze(self, data: Dict[str, Any]) -> bool:
        """Validate generation data at Bronze layer"""
        required_fields = ['date', 'generation_values']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Validate date format
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            logger.error("Invalid date format in generation data")
            return False
            
        # Validate generation values
        if not isinstance(data['generation_values'], list):
            logger.error("Generation values must be a list")
            return False
            
        # Validate individual generation entries
        for entry in data['generation_values']:
            if not isinstance(entry, dict):
                logger.error("Each generation entry must be a dictionary")
                return False
                
            required_entry_fields = ['timestamp', 'value', 'fuel_type']
            for field in required_entry_fields:
                if field not in entry:
                    logger.error(f"Missing required entry field: {field}")
                    return False
                    
            # Validate timestamp format
            try:
                datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                logger.error("Invalid timestamp format in generation data")
                return False
                
            # Validate value is numeric
            if not isinstance(entry['value'], (int, float)):
                logger.error("Generation value must be numeric")
                return False
                
        return True

    def validate_silver_data(self, df: pd.DataFrame, data_type: str) -> bool:
        """
        Validate Silver layer data
        
        Args:
            df: Pandas DataFrame with processed data
            data_type: Type of data ('demand', 'weather', 'generation')
            
        Returns:
            bool: True if data passes validation, False otherwise
        """
        logger.info(f"Validating {data_type} data at Silver layer")
        
        try:
            if data_type == 'demand':
                return self._validate_demand_silver(df)
            elif data_type == 'weather':
                return self._validate_weather_silver(df)
            elif data_type == 'generation':
                return self._validate_generation_silver(df)
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return False
                
        except Exception as e:
            logger.error(f"Silver validation error for {data_type}: {str(e)}")
            return False

    def _validate_demand_silver(self, df: pd.DataFrame) -> bool:
        """Validate demand data at Silver layer"""
        required_columns = ['date', 'timestamp', 'value']
        
        # Check required columns
        for column in required_columns:
            if column not in df.columns:
                logger.error(f"Missing required column: {column}")
                return False
                
        # Validate data types
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            logger.error("Timestamp column must be datetime type")
            return False
            
        if not pd.api.types.is_numeric_dtype(df['value']):
            logger.error("Value column must be numeric type")
            return False
            
        # Check for null values
        if df[['date', 'timestamp', 'value']].isnull().any().any():
            logger.error("Null values found in required columns")
            return False
            
        return True

    def _validate_weather_silver(self, df: pd.DataFrame) -> bool:
        """Validate weather data at Silver layer"""
        required_columns = ['latitude', 'longitude', 'timestamp', 'temperature', 'humidity']
        
        # Check required columns
        for column in required_columns:
            if column not in df.columns:
                logger.error(f"Missing required column: {column}")
                return False
                
        # Validate data types
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            logger.error("Timestamp column must be datetime type")
            return False
            
        if not pd.api.types.is_numeric_dtype(df['temperature']):
            logger.error("Temperature column must be numeric type")
            return False
            
        if not pd.api.types.is_numeric_dtype(df['humidity']):
            logger.error("Humidity column must be numeric type")
            return False
            
        # Check for null values
        if df[['latitude', 'longitude', 'timestamp', 'temperature', 'humidity']].isnull().any().any():
            logger.error("Null values found in required columns")
            return False
            
        return True

    def _validate_generation_silver(self, df: pd.DataFrame) -> bool:
        """Validate generation data at Silver layer"""
        required_columns = ['date', 'timestamp', 'value', 'fuel_type']
        
        # Check required columns
        for column in required_columns:
            if column not in df.columns:
                logger.error(f"Missing required column: {column}")
                return False
                
        # Validate data types
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            logger.error("Timestamp column must be datetime type")
            return False
            
        if not pd.api.types.is_numeric_dtype(df['value']):
            logger.error("Value column must be numeric type")
            return False
            
        # Check for null values
        if df[['date', 'timestamp', 'value', 'fuel_type']].isnull().any().any():
            logger.error("Null values found in required columns")
            return False
            
        return True

    def generate_quality_report(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quality report for data
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            data: Raw data
            
        Returns:
            Dict with quality metrics
        """
        report = {
            'data_type': data_type,
            'timestamp': datetime.utcnow().isoformat(),
            'validation_passed': self.validate_bronze_data(data, data_type),
            'data_size': len(str(data)) if data else 0,
            'fields_count': len(data) if data else 0
        }
        
        return report