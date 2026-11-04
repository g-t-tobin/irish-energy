from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class DemandData(BaseModel):
    timestamp: datetime
    demand_mw: float
    demand_mwh: float
    forecast_mw: float
    forecast_mwh: float

class WeatherData(BaseModel):
    timestamp: datetime
    temperature_celsius: float
    humidity_percent: float
    wind_speed_mps: float
    wind_direction_degrees: float
    pressure_hpa: float
    precipitation_mm: float

class GenerationData(BaseModel):
    timestamp: datetime
    renewable_generation_mw: float
    fossil_generation_mw: float
    nuclear_generation_mw: float
    total_generation_mw: float

class DataQualityMetrics(BaseModel):
    dataset_name: str
    total_records: int
    missing_values: int
    data_quality_score: float
    last_updated: datetime

class SummaryData(BaseModel):
    total_datasets: int
    total_records: int
    last_updated: datetime
    data_quality_summary: dict