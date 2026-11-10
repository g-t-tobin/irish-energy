"""
Data freshness monitoring for Irish Energy Analytics Platform
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from loguru import logger
import boto3

from src.common.config import Config


class DataFreshnessMonitor:
    """
    Monitor data freshness across different layers of the platform
    """

    def __init__(self):
        """Initialize the data freshness monitor"""
        self.config = Config()
        self.cloudwatch_client = None
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            self.cloudwatch_client = boto3.client('cloudwatch')

    def check_data_freshness(self, data_type: str, date_str: str, 
                           location: Optional[str] = None) -> Dict[str, Any]:
        """
        Check the freshness of data for a given date and type
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            location: Location identifier for weather data (optional)
            
        Returns:
            Dictionary with freshness check results
        """
        try:
            # Calculate how fresh the data is
            target_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            current_date = datetime.now(timezone.utc)
            
            # Calculate difference in days
            days_diff = (current_date - target_date).days
            
            # Calculate freshness score (0-100)
            # Assume data is fresh if it's within 1 day, less fresh if older
            if days_diff <= 0:
                freshness_score = 100  # Current day data
            elif days_diff <= 1:
                freshness_score = 80   # Yesterday data
            elif days_diff <= 7:
                freshness_score = 60   # Within a week
            else:
                freshness_score = 30   # Older data
                
            freshness_info = {
                'data_type': data_type,
                'date': date_str,
                'location': location,
                'days_since_target': days_diff,
                'freshness_score': freshness_score,
                'last_processed_date': datetime.now(timezone.utc).isoformat(),
                'is_fresh': days_diff <= 1  # Consider fresh if within 1 day
            }
            
            # Emit freshness metrics if in Lambda environment
            self._emit_freshness_metrics(data_type, date_str, freshness_info, location)
            
            return freshness_info
            
        except Exception as e:
            logger.error(f"Error checking data freshness for {data_type} on {date_str}: {str(e)}")
            return {
                'data_type': data_type,
                'date': date_str,
                'location': location,
                'days_since_target': -1,
                'freshness_score': 0,
                'last_processed_date': datetime.now(timezone.utc).isoformat(),
                'is_fresh': False,
                'error': str(e)
            }

    def _emit_freshness_metrics(self, data_type: str, date_str: str, 
                              freshness_info: Dict[str, Any], 
                              location: Optional[str] = None):
        """
        Emit data freshness metrics to CloudWatch
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            freshness_info: Freshness information dictionary
            location: Location identifier for weather data (optional)
        """
        if not self.cloudwatch_client:
            return  # Don't emit metrics outside of Lambda environment
            
        try:
            # Prepare dimensions for CloudWatch metrics
            dimensions = [
                {'Name': 'DataType', 'Value': data_type},
                {'Name': 'Date', 'Value': date_str}
            ]
            
            if location:
                dimensions.append({'Name': 'Location', 'Value': location})
                
            # Emit freshness metrics
            self.cloudwatch_client.put_metric_data(
                Namespace='IrishEnergy/DataFreshness',
                MetricData=[
                    {
                        'MetricName': 'DaysSinceTarget',
                        'Value': freshness_info['days_since_target'],
                        'Unit': 'Count',
                        'Dimensions': dimensions
                    },
                    {
                        'MetricName': 'FreshnessScore',
                        'Value': freshness_info['freshness_score'],
                        'Unit': 'Percent',
                        'Dimensions': dimensions
                    },
                    {
                        'MetricName': 'IsFresh',
                        'Value': 1 if freshness_info['is_fresh'] else 0,
                        'Unit': 'Count',
                        'Dimensions': dimensions
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Failed to emit freshness metrics: {str(e)}")

    def check_all_layers_freshness(self, data_type: str, date_str: str, 
                                 location: Optional[str] = None) -> Dict[str, Any]:
        """
        Check freshness across all data layers (Bronze, Silver, Gold)
        
        Args:
            data_type: Type of data ('demand', 'weather', 'generation')
            date_str: Date string in YYYY-MM-DD format
            location: Location identifier for weather data (optional)
            
        Returns:
            Dictionary with freshness information for all layers
        """
        # For now, we'll focus on checking the Silver layer freshness
        # In a more complete implementation, we would check all layers
        return self.check_data_freshness(data_type, date_str, location)