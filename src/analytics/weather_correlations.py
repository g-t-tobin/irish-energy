"""
Weather and demand correlation analysis module for Irish Energy Analytics Data Platform
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from scipy.stats import pearsonr, spearmanr
from src.analytics.models import CorrelationAnalysisResult
from src.analytics.data_access import GoldDataAccessor

class WeatherDemandCorrelationAnalyzer:
    """Analyzer for weather-demand correlation data"""

    def __init__(self, data_accessor: GoldDataAccessor):
        self.data_accessor = data_accessor

    def analyze_weather_demand_correlations(self,
                                           start_date: Optional[str] = None,
                                           end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive weather-demand correlation analysis
        
        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            Dictionary with comprehensive weather-demand correlation analysis
        """
        # Get demand and weather data
        demand_df = self.data_accessor.get_demand_data(start_date, end_date)
        weather_df = self.data_accessor.get_weather_data(start_date, end_date)

        if demand_df.empty or weather_df.empty:
            raise ValueError("Insufficient data for correlation analysis")

        # Align timestamps - find overlapping periods
        aligned_data = self._align_weather_and_demand(demand_df, weather_df)
        
        if aligned_data is None or len(aligned_data) < 2:
            raise ValueError("Insufficient aligned data for correlation analysis")

        # Calculate correlation coefficients
        pearson_corr, spearman_corr = self._calculate_correlations(aligned_data)
        
        # Determine correlation strength
        correlation_strength = self._determine_correlation_strength(pearson_corr)
        
        # Extract key findings
        key_findings = self._extract_key_findings(pearson_corr, spearman_corr, aligned_data)
        
        # Get date range
        date_range = (aligned_data['timestamp'].min().strftime('%Y-%m-%d'),
                     aligned_data['timestamp'].max().strftime('%Y-%m-%d'))

        return {
            "dataset_names": ["demand", "weather"],
            "date_range": date_range,
            "pearson_correlation": pearson_corr,
            "spearman_correlation": spearman_corr,
            "sample_size": len(aligned_data),
            "correlation_strength": correlation_strength,
            "key_findings": key_findings,
            "calculation_timestamp": datetime.now().isoformat()
        }

    def _align_weather_and_demand(self, demand_df: pd.DataFrame, weather_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Align weather and demand data by timestamp
        
        Returns:
            Aligned DataFrame or None if insufficient overlap
        """
        # Convert timestamps to datetime if needed
        demand_df = demand_df.copy()
        weather_df = weather_df.copy()
        
        # Ensure timestamp columns are datetime
        demand_df['timestamp'] = pd.to_datetime(demand_df['timestamp'])
        weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
        
        # Merge on timestamp (inner join to get aligned data)
        merged_df = pd.merge(demand_df, weather_df, on='timestamp', how='inner')
        
        # Check if we have sufficient data
        if len(merged_df) < 2:
            return None
            
        return merged_df

    def _calculate_correlations(self, aligned_df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate Pearson and Spearman correlation coefficients
        
        Returns:
            Tuple of (pearson_correlation, spearman_correlation)
        """
        try:
            # Default to None if no data
            pearson_corr = None
            spearman_corr = None
            
            # Check if we have enough data for correlation
            if len(aligned_df) >= 2:
                # Correlate demand with temperature
                if 'temperature_celsius' in aligned_df.columns and 'demand_mw' in aligned_df.columns:
                    pearson_corr, _ = pearsonr(aligned_df['demand_mw'], aligned_df['temperature_celsius'])
                    spearman_corr, _ = spearmanr(aligned_df['demand_mw'], aligned_df['temperature_celsius'])
                    
            return pearson_corr, spearman_corr
            
        except Exception:
            # Return None if correlation calculation fails
            return None, None

    def _determine_correlation_strength(self, pearson_corr: Optional[float]) -> str:
        """
        Determine correlation strength based on Pearson coefficient
        
        Returns:
            String indicating correlation strength
        """
        if pearson_corr is None:
            return "insufficient"
            
        corr_abs = abs(pearson_corr)
        
        if corr_abs >= 0.7:
            return "strong"
        elif corr_abs >= 0.3:
            return "moderate"
        elif corr_abs >= 0.1:
            return "weak"
        else:
            return "very_weak"

    def _extract_key_findings(self, pearson_corr: Optional[float], spearman_corr: Optional[float], aligned_df: pd.DataFrame) -> List[str]:
        """
        Extract key findings from correlation analysis
        
        Returns:
            List of key findings
        """
        findings = []
        
        # Basic correlation findings
        if pearson_corr is not None:
            if abs(pearson_corr) > 0.1:
                direction = "positive" if pearson_corr > 0 else "negative"
                findings.append(f"Detected {direction} correlation ({pearson_corr:.3f}) between demand and temperature")
        
        # Temperature extremes
        if 'temperature_celsius' in aligned_df.columns:
            temp_min = aligned_df['temperature_celsius'].min()
            temp_max = aligned_df['temperature_celsius'].max()
            findings.append(f"Temperature range: {temp_min:.1f}°C to {temp_max:.1f}°C")
            
            # Find extreme temperature periods
            hot_periods = aligned_df[aligned_df['temperature_celsius'] > 25]
            cold_periods = aligned_df[aligned_df['temperature_celsius'] < 5]
            
            if len(hot_periods) > 0:
                findings.append(f"Observed {len(hot_periods)} periods with temperature above 25°C")
            if len(cold_periods) > 0:
                findings.append(f"Observed {len(cold_periods)} periods with temperature below 5°C")
        
        # Demand extremes
        if 'demand_mw' in aligned_df.columns:
            demand_min = aligned_df['demand_mw'].min()
            demand_max = aligned_df['demand_mw'].max()
            findings.append(f"Demand range: {demand_min:.1f} MW to {demand_max:.1f} MW")
            
            # Find peak demand periods
            peak_demand_periods = aligned_df[aligned_df['demand_mw'] > aligned_df['demand_mw'].quantile(0.9)]
            if len(peak_demand_periods) > 0:
                findings.append(f"Observed {len(peak_demand_periods)} peak demand periods")
        
        # Weather patterns
        if 'humidity_percent' in aligned_df.columns:
            avg_humidity = aligned_df['humidity_percent'].mean()
            findings.append(f"Average humidity: {avg_humidity:.1f}%")
            
        if 'wind_speed_mps' in aligned_df.columns:
            avg_wind = aligned_df['wind_speed_mps'].mean()
            findings.append(f"Average wind speed: {avg_wind:.2f} m/s")
            
        return findings

    def analyze_weather_demand_patterns(self,
                                       start_date: Optional[str] = None,
                                       end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze weather-demand patterns beyond simple correlation
        
        Args:
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            Dictionary with weather-demand pattern analysis
        """
        # Get demand and weather data
        demand_df = self.data_accessor.get_demand_data(start_date, end_date)
        weather_df = self.data_accessor.get_weather_data(start_date, end_date)

        if demand_df.empty or weather_df.empty:
            raise ValueError("Insufficient data for pattern analysis")

        # Align timestamps
        aligned_data = self._align_weather_and_demand(demand_df, weather_df)
        
        if aligned_data is None or len(aligned_data) < 2:
            raise ValueError("Insufficient aligned data for pattern analysis")

        # Calculate temperature-demand relationship
        temp_demand_relationship = self._calculate_temp_demand_relationship(aligned_data)
        
        # Calculate seasonal patterns
        seasonal_patterns = self._calculate_seasonal_patterns(aligned_data)
        
        # Calculate hourly patterns
        hourly_patterns = self._calculate_hourly_patterns(aligned_data)
        
        # Get date range
        date_range = (aligned_data['timestamp'].min().strftime('%Y-%m-%d'),
                     aligned_data['timestamp'].max().strftime('%Y-%m-%d'))

        return {
            "dataset_names": ["demand", "weather"],
            "date_range": date_range,
            "temperature_demand_relationship": temp_demand_relationship,
            "seasonal_patterns": seasonal_patterns,
            "hourly_patterns": hourly_patterns,
            "sample_size": len(aligned_data),
            "calculation_timestamp": datetime.now().isoformat()
        }

    def _calculate_temp_demand_relationship(self, aligned_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate temperature-demand relationship"""
        if 'temperature_celsius' not in aligned_df.columns or 'demand_mw' not in aligned_df.columns:
            return {}
            
        # Group by temperature bins
        aligned_df['temp_bin'] = pd.cut(aligned_df['temperature_celsius'], 
                                      bins=10, 
                                      include_lowest=True)
        
        temp_demand_stats = aligned_df.groupby('temp_bin')['demand_mw'].agg(['mean', 'std', 'count']).reset_index()
        
        return {
            "temperature_bins": temp_demand_stats['temp_bin'].tolist(),
            "average_demand_by_temp": temp_demand_stats['mean'].tolist(),
            "std_demand_by_temp": temp_demand_stats['std'].tolist(),
            "count_by_temp": temp_demand_stats['count'].tolist()
        }

    def _calculate_seasonal_patterns(self, aligned_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate seasonal patterns"""
        if 'timestamp' not in aligned_df.columns:
            return {}
            
        df_copy = aligned_df.copy()
        df_copy['month'] = df_copy['timestamp'].dt.month
        
        # Define seasons
        def get_season(month):
            if month in [12, 1, 2]:
                return 'Winter'
            elif month in [3, 4, 5]:
                return 'Spring'
            elif month in [6, 7, 8]:
                return 'Summer'
            else:
                return 'Fall'
        
        df_copy['season'] = df_copy['month'].apply(get_season)
        
        if 'demand_mw' in df_copy.columns:
            seasonal_avg = df_copy.groupby('season')['demand_mw'].mean().to_dict()
            return seasonal_avg
            
        return {}

    def _calculate_hourly_patterns(self, aligned_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate hourly demand patterns"""
        if 'timestamp' not in aligned_df.columns or 'demand_mw' not in aligned_df.columns:
            return {}
            
        df_copy = aligned_df.copy()
        df_copy['hour'] = df_copy['timestamp'].dt.hour
        
        hourly_avg = df_copy.groupby('hour')['demand_mw'].mean().to_dict()
        return hourly_avg