"""
Analytics models for Irish Energy Analytics Data Platform
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

@dataclass
class DemandAnalysisResult:
    """Result of electricity demand analysis"""
    dataset_name: str
    date_range: Tuple[str, str]
    total_demand_mwh: float
    average_demand_mw: float
    min_demand_mw: float
    max_demand_mw: float
    median_demand_mw: float
    peak_demand_periods: List[Dict[str, Any]]
    daily_profiles: Dict[str, float]
    weekly_patterns: Dict[str, float]
    monthly_patterns: Dict[str, float]
    seasonal_patterns: Dict[str, float]
    growth_rate: Optional[float] = None
    calculation_timestamp: str = None

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()

@dataclass
class GenerationAnalysisResult:
    """Result of electricity generation analysis"""
    dataset_name: str
    date_range: Tuple[str, str]
    total_generation_mw: float
    renewable_generation_mw: float
    fossil_generation_mw: float
    nuclear_generation_mw: float
    generation_mix: Dict[str, float]
    daily_trends: Dict[str, float]
    monthly_trends: Dict[str, float]
    fuel_type_breakdown: Dict[str, float]
    calculation_timestamp: str = None

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()

@dataclass
class RenewableAnalysisResult:
    """Result of renewable energy analysis"""
    dataset_name: str
    date_range: Tuple[str, str]
    renewable_generation_mw: float
    total_generation_mw: float
    renewable_share_percentage: float
    renewable_trends: Dict[str, float]
    seasonal_contribution: Dict[str, float]
    peak_renewable_periods: List[Dict[str, Any]]
    wind_generation_mw: Optional[float] = None
    solar_generation_mw: Optional[float] = None
    calculation_timestamp: str = None

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()

@dataclass
class WeatherAnalysisResult:
    """Result of weather analysis"""
    dataset_name: str
    date_range: Tuple[str, str]
    avg_temperature_celsius: float
    avg_humidity_percent: float
    avg_wind_speed_mps: float
    avg_precipitation_mm: float
    temperature_trends: Dict[str, float]
    precipitation_trends: Dict[str, float]
    weather_patterns: Dict[str, float]
    seasonal_weather: Dict[str, float]
    calculation_timestamp: str = None

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()

@dataclass
class CorrelationAnalysisResult:
    """Result of weather-demand correlation analysis"""
    dataset_names: List[str]
    date_range: Tuple[str, str]
    pearson_correlation: Optional[float] = None
    spearman_correlation: Optional[float] = None
    sample_size: int = 0
    correlation_strength: str = "insufficient"
    key_findings: List[str] = None
    calculation_timestamp: str = None

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()
        if self.key_findings is None:
            self.key_findings = []

@dataclass
class StatisticalAnalysisResult:
    """Result of statistical analysis"""
    dataset_name: str
    date_range: Tuple[str, str]
    rolling_averages: Dict[str, List[float]]
    percentage_changes: Dict[str, List[float]]
    standard_deviations: Dict[str, float]
    interquartile_ranges: Dict[str, float]
    trends: Dict[str, str]
    outliers: List[Dict[str, Any]]
    distribution_summary: Dict[str, Any]
    calculation_timestamp: str = None

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()

@dataclass
class PeakDemandAnalysisResult:
    """Result of peak demand analysis"""
    dataset_name: str
    date_range: Tuple[str, str]
    highest_recorded_demand_mw: float
    lowest_recorded_demand_mw: float
    average_demand_mw: float
    median_demand_mw: float
    highest_demand_period: Dict[str, Any]
    lowest_demand_period: Dict[str, Any]
    daily_peak_demands: Dict[str, float]
    weekly_peak_demands: Dict[str, float]
    monthly_peak_demands: Dict[str, float]
    peak_timing_analysis: Dict[str, Any]
    demand_variability: Dict[str, float]
    historical_comparisons: Dict[str, Any]
    calculation_timestamp: str = None

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()

@dataclass
class AnalyticalReport:
    """Structured analytical report"""
    report_name: str
    dataset_references: List[str]
    date_range: Tuple[str, str]
    observation_count: int
    calculation_timestamp: str
    metrics: Dict[str, Any]
    key_findings: List[str]
    statistical_results: Dict[str, Any]
    limitations: List[str]
    data_quality_considerations: List[str]
    calculation_parameters: Dict[str, Any]

    def __post_init__(self):
        if self.calculation_timestamp is None:
            self.calculation_timestamp = datetime.now().isoformat()
        if self.key_findings is None:
            self.key_findings = []
        if self.statistical_results is None:
            self.statistical_results = {}
        if self.limitations is None:
            self.limitations = []
        if self.data_quality_considerations is None:
            self.data_quality_considerations = []
        if self.calculation_parameters is None:
            self.calculation_parameters = {}