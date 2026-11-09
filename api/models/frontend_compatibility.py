"""
Frontend-compatible data models for Irish Energy Analytics API
These models translate API data structures to match frontend expectations
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from .models_definitions import DemandData as APIDemandData, \
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
def convert_api_to_frontend_demand(api_data: List[Dict[str, Any]]) -> List[FrontendDemandData]:
    """Convert API demand data to frontend-compatible format"""
    result = []
    for item in api_data:
        # The item should already be in the correct format from the data service
        frontend_item = FrontendDemandData(**item)
        result.append(frontend_item)
    return result

def convert_api_to_frontend_weather(api_data: List[Dict[str, Any]]) -> List[FrontendWeatherData]:
    """Convert API weather data to frontend-compatible format"""
    result = []
    for item in api_data:
        # The item should already be in the correct format from the data service
        frontend_item = FrontendWeatherData(**item)
        result.append(frontend_item)
    return result

def convert_api_to_frontend_generation(api_data: List[Dict[str, Any]]) -> List[FrontendGenerationData]:
    """Convert API generation data to frontend-compatible format"""
    result = []
    for item in api_data:
        # The item should already be in the correct format from the data service
        frontend_item = FrontendGenerationData(**item)
        result.append(frontend_item)
    return result

def convert_api_to_frontend_quality(api_data: List[Dict[str, Any]]) -> List[FrontendDataQualityMetrics]:
    """Convert API quality metrics to frontend-compatible format"""
    result = []
    for item in api_data:
        # For quality metrics, we need to adjust the data structure to match frontend expectations
        frontend_item = FrontendDataQualityMetrics(
            data_type=item["dataset_name"],
            date=item["last_updated"].strftime('%Y-%m-%d'),
            bronze_processed=True,  # Placeholder - would need actual data
            silver_processed=True,  # Placeholder - would need actual data
            gold_processed=True,    # Placeholder - would need actual data
            processing_timestamp=item["last_updated"].isoformat()
        )
        result.append(frontend_item)
    return result

def convert_api_to_frontend_summary(api_data: Dict[str, Any]) -> FrontendSummaryData:
    """Convert API summary data to frontend-compatible format"""
    # Adjust the data structure to match the expected frontend format
    return FrontendSummaryData(
        total_datasets=api_data["total_datasets"],
        total_records=api_data["total_records"],
        last_updated=api_data["last_updated"].strftime('%Y-%m-%d'),
        data_quality_summary=api_data["data_quality_summary"]
    )