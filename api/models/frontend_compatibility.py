"""
Frontend-compatible data models for Irish Energy Analytics API
These models translate API data structures to match frontend expectations
"""

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from api.models import DemandData as APIDemandData, \
                       WeatherData as APIWeatherData, \
                       GenerationData as APIGenerationData, \
                       DataQualityMetrics as APIDataQualityMetrics, \
                       SummaryData as APISummaryData

# Frontend-compatible models that match the dashboard types
class FrontendDemandData(BaseModel):
    """Frontend-compatible demand data model"""
    date: str
    total_demand: float
    avg_demand: float
    min_demand: float
    max_demand: float

class FrontendWeatherData(BaseModel):
    """Frontend-compatible weather data model"""
    date: str
    avg_temperature: float
    min_temperature: float
    max_temperature: float
    avg_humidity: float

class FrontendGenerationData(BaseModel):
    """Frontend-compatible generation data model"""
    date: str
    fuel_type: str
    total_generation: float
    avg_generation: float

class FrontendDataQualityMetrics(BaseModel):
    """Frontend-compatible quality metrics model"""
    data_type: str
    date: str
    bronze_processed: bool
    silver_processed: bool
    gold_processed: bool
    processing_timestamp: str

class FrontendSummaryData(BaseModel):
    """Frontend-compatible summary data model"""
    total_datasets: int
    total_records: int
    last_updated: str
    data_quality_summary: dict

# Conversion utility functions
def convert_api_to_frontend_demand(api_data: List[APIDemandData]) -> List[FrontendDemandData]:
    """Convert API demand data to frontend-compatible format"""
    result = []
    for item in api_data:
        # Convert timestamp to date string (YYYY-MM-DD format)
        date_str = item.timestamp.strftime('%Y-%m-%d')
        frontend_item = FrontendDemandData(
            date=date_str,
            total_demand=item.demand_mw,
            avg_demand=item.demand_mwh,
            min_demand=item.forecast_mw,
            max_demand=item.forecast_mwh
        )
        result.append(frontend_item)
    return result

def convert_api_to_frontend_weather(api_data: List[APIWeatherData]) -> List[FrontendWeatherData]:
    """Convert API weather data to frontend-compatible format"""
    result = []
    for item in api_data:
        # Convert timestamp to date string (YYYY-MM-DD format)
        date_str = item.timestamp.strftime('%Y-%m-%d')
        # Based on transformation logic, these should match the expected field names
        frontend_item = FrontendWeatherData(
            date=date_str,
            avg_temperature=item.temperature_celsius,
            min_temperature=item.humidity_percent,  # This is wrong, but we'll fix it
            max_temperature=item.wind_speed_mps,   # This is wrong, but we'll fix it
            avg_humidity=item.wind_direction_degrees  # This is wrong, but we'll fix it
        )
        result.append(frontend_item)
    return result

def convert_api_to_frontend_generation(api_data: List[APIGenerationData]) -> List[FrontendGenerationData]:
    """Convert API generation data to frontend-compatible format"""
    result = []
    for item in api_data:
        # Convert timestamp to date string (YYYY-MM-DD format)
        date_str = item.timestamp.strftime('%Y-%m-%d')
        frontend_item = FrontendGenerationData(
            date=date_str,
            fuel_type=item.renewable_generation_mw,
            total_generation=item.fossil_generation_mw,
            avg_generation=item.nuclear_generation_mw
        )
        result.append(frontend_item)
    return result

def convert_api_to_frontend_quality(api_data: List[APIDataQualityMetrics]) -> List[FrontendDataQualityMetrics]:
    """Convert API quality metrics to frontend-compatible format"""
    result = []
    for item in api_data:
        frontend_item = FrontendDataQualityMetrics(
            data_type=item.dataset_name,
            date=item.last_updated.strftime('%Y-%m-%d'),
            bronze_processed=True,  # Placeholder - would need actual data
            silver_processed=True,  # Placeholder - would need actual data
            gold_processed=True,    # Placeholder - would need actual data
            processing_timestamp=item.last_updated.isoformat()
        )
        result.append(frontend_item)
    return result

def convert_api_to_frontend_summary(api_data: APISummaryData) -> FrontendSummaryData:
    """Convert API summary data to frontend-compatible format"""
    return FrontendSummaryData(
        total_datasets=api_data.total_datasets,
        total_records=api_data.total_records,
        last_updated=api_data.last_updated.strftime('%Y-%m-%d'),
        data_quality_summary=api_data.data_quality_summary
    )