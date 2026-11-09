"""
Daily aggregation functions for Irish Energy Analytics data.

These functions handle the conversion of raw observations into daily aggregates
that match the expected frontend data structure.
"""

from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from models.models_definitions import DemandData, WeatherData, GenerationData
from models.frontend_compatibility import (
    FrontendDemandData, FrontendWeatherData, FrontendGenerationData
)


def aggregate_demand_by_day(api_data: List[DemandData]) -> List[FrontendDemandData]:
    """
    Aggregate demand data by day with proper statistical calculations.

    Args:
        api_data: List of raw DemandData observations

    Returns:
        List of FrontendDemandData with daily aggregates
    """
    # Group observations by date
    daily_groups = defaultdict(list)
    for item in api_data:
        date_str = item.timestamp.strftime('%Y-%m-%d')
        daily_groups[date_str].append(item)

    result = []
    for date_str, observations in daily_groups.items():
        # Extract all values for this date
        demand_mw_values = [obs.demand_mw for obs in observations if obs.demand_mw is not None]
        demand_mwh_values = [obs.demand_mwh for obs in observations if obs.demand_mwh is not None]
        forecast_mw_values = [obs.forecast_mw for obs in observations if obs.forecast_mw is not None]
        forecast_mwh_values = [obs.forecast_mwh for obs in observations if obs.forecast_mwh is not None]

        # Skip if no valid data
        if not demand_mw_values and not demand_mwh_values and not forecast_mw_values and not forecast_mwh_values:
            continue

        # Calculate statistics
        avg_demand = sum(demand_mwh_values) / len(demand_mwh_values) if demand_mwh_values else 0.0
        min_demand = min(forecast_mw_values) if forecast_mw_values else 0.0
        max_demand = max(forecast_mwh_values) if forecast_mwh_values else 0.0
        # For peak demand, we'll use the highest actual demand value
        peak_demand = max(demand_mw_values) if demand_mw_values else 0.0

        # Use first available timestamp for date
        frontend_item = FrontendDemandData(
            date=date_str,
            total_demand=max(demand_mw_values) if demand_mw_values else 0.0,
            avg_demand=avg_demand,
            min_demand=min_demand,
            max_demand=max_demand
        )
        result.append(frontend_item)

    return result


def aggregate_weather_by_day(api_data: List[WeatherData]) -> List[FrontendWeatherData]:
    """
    Aggregate weather data by day with proper statistical calculations.

    Args:
        api_data: List of raw WeatherData observations

    Returns:
        List of FrontendWeatherData with daily aggregates
    """
    # Group observations by date
    daily_groups = defaultdict(list)
    for item in api_data:
        date_str = item.timestamp.strftime('%Y-%m-%d')
        daily_groups[date_str].append(item)

    result = []
    for date_str, observations in daily_groups.items():
        # Extract all values for this date
        temp_values = [obs.temperature_celsius for obs in observations if obs.temperature_celsius is not None]
        humidity_values = [obs.humidity_percent for obs in observations if obs.humidity_percent is not None]
        wind_speed_values = [obs.wind_speed_mps for obs in observations if obs.wind_speed_mps is not None]
        precip_values = [obs.precipitation_mm for obs in observations if obs.precipitation_mm is not None]

        # Skip if no valid data
        if not temp_values and not humidity_values and not wind_speed_values:
            continue

        # Calculate statistics
        avg_temp = sum(temp_values) / len(temp_values) if temp_values else 0.0
        min_temp = min(temp_values) if temp_values else 0.0
        max_temp = max(temp_values) if temp_values else 0.0
        avg_humidity = sum(humidity_values) / len(humidity_values) if humidity_values else 0.0
        avg_wind_speed = sum(wind_speed_values) / len(wind_speed_values) if wind_speed_values else 0.0
        total_precipitation = sum(precip_values) if precip_values else 0.0

        # Use first available timestamp for date
        frontend_item = FrontendWeatherData(
            date=date_str,
            avg_temperature=avg_temp,
            min_temperature=min_temp,
            max_temperature=max_temp,
            avg_humidity=avg_humidity
        )
        result.append(frontend_item)

    return result


def aggregate_generation_by_day(api_data: List[GenerationData]) -> List[FrontendGenerationData]:
    """
    Aggregate generation data by day and fuel type with proper statistical calculations.

    Args:
        api_data: List of raw GenerationData observations

    Returns:
        List of FrontendGenerationData with daily aggregates by fuel type
    """
    # Group observations by date
    daily_groups = defaultdict(list)
    for item in api_data:
        date_str = item.timestamp.strftime('%Y-%m-%d')
        daily_groups[date_str].append(item)

    result = []
    for date_str, observations in daily_groups.items():
        # Process each fuel type separately
        fuel_types = ['renewable', 'fossil', 'nuclear']

        for fuel_type in fuel_types:
            # Get values for this fuel type
            if fuel_type == 'renewable':
                values = [obs.renewable_generation_mw for obs in observations
                         if obs.renewable_generation_mw is not None]
                total_field = 'renewable_generation_mw'
            elif fuel_type == 'fossil':
                values = [obs.fossil_generation_mw for obs in observations
                         if obs.fossil_generation_mw is not None]
                total_field = 'fossil_generation_mw'
            else:  # nuclear
                values = [obs.nuclear_generation_mw for obs in observations
                         if obs.nuclear_generation_mw is not None]
                total_field = 'nuclear_generation_mw'

            # Skip if no valid data
            if not values:
                continue

            # Calculate statistics
            avg_generation = sum(values) / len(values) if values else 0.0
            max_generation = max(values) if values else 0.0

            # Create frontend item
            frontend_item = FrontendGenerationData(
                date=date_str,
                fuel_type=fuel_type,
                total_generation=max_generation,  # Peak generation for the day
                avg_generation=avg_generation
            )
            result.append(frontend_item)

    return result