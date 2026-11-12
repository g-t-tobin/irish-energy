"""
Analytics API endpoints for Irish Energy Analytics Data Platform
"""
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from loguru import logger

# Import analytics modules
from src.analytics.demand import DemandAnalyzer
from src.analytics.generation import GenerationAnalyzer
from src.analytics.renewables import RenewableAnalyzer
from src.analytics.weather import WeatherAnalyzer
from src.analytics.correlations import CorrelationAnalyzer
from src.analytics.statistics import StatisticalAnalyzer
from src.analytics.peak_demand import PeakDemandAnalyzer
from src.analytics.historical_demand import HistoricalDemandAnalyzer
from src.analytics.generation_mix import GenerationMixAnalyzer
from src.analytics.renewable_penetration import RenewablePenetrationAnalyzer
from src.analytics.weather_correlations import WeatherDemandCorrelationAnalyzer
from src.analytics.reporting import ReportingEngine
from src.analytics.data_access import GoldDataAccessor
from src.analytics.models import (
    DemandAnalysisResult,
    GenerationAnalysisResult,
    RenewableAnalysisResult,
    WeatherAnalysisResult,
    CorrelationAnalysisResult,
    StatisticalAnalysisResult,
    AnalyticalReport
)

# Initialize data accessor
data_accessor = GoldDataAccessor()

# Initialize analyzers
demand_analyzer = DemandAnalyzer(data_accessor)
generation_analyzer = GenerationAnalyzer(data_accessor)
renewable_analyzer = RenewableAnalyzer(data_accessor)
weather_analyzer = WeatherAnalyzer(data_accessor)
correlation_analyzer = CorrelationAnalyzer(data_accessor)
statistical_analyzer = StatisticalAnalyzer(data_accessor)
peak_demand_analyzer = PeakDemandAnalyzer(data_accessor)
historical_demand_analyzer = HistoricalDemandAnalyzer(data_accessor)
generation_mix_analyzer = GenerationMixAnalyzer(data_accessor)
renewable_penetration_analyzer = RenewablePenetrationAnalyzer(data_accessor)
weather_correlation_analyzer = WeatherDemandCorrelationAnalyzer(data_accessor)
reporting_engine = ReportingEngine()

# Define the API routes for analytics functionality
# Note: This will be mounted under /analytics in main.py
app = FastAPI(title="Analytics API", version="1.0.0")


@app.get("/health", response_model=dict)
async def analytics_health_check():
    """Health check endpoint for analytics service"""
    return {"status": "healthy", "service": "analytics"}


@app.get("/demand/trends", response_model=Dict[str, Any])
async def get_demand_trends(start_date: str = None, end_date: str = None):
    """
    Get demand trends analysis

    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = demand_analyzer.analyze_demand(start_date, end_date)
        # Convert to serializable dict
        return {
            "dataset_name": result.dataset_name,
            "date_range": result.date_range,
            "total_demand_mwh": result.total_demand_mwh,
            "average_demand_mw": result.average_demand_mw,
            "min_demand_mw": result.min_demand_mw,
            "max_demand_mw": result.max_demand_mw,
            "median_demand_mw": result.median_demand_mw,
            "peak_demand_periods": result.peak_demand_periods,
            "daily_profiles": result.daily_profiles,
            "weekly_patterns": result.weekly_patterns,
            "monthly_patterns": result.monthly_patterns,
            "seasonal_patterns": result.seasonal_patterns,
            "growth_rate": result.growth_rate,
            "calculation_timestamp": result.calculation_timestamp
        }
    except Exception as e:
        logger.error(f"Error in demand trends analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in demand analysis: {str(e)}")


@app.get("/demand/peaks", response_model=Dict[str, Any])
async def get_demand_peaks(start_date: str = None, end_date: str = None):
    """
    Get peak demand identification

    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = demand_analyzer.analyze_demand(start_date, end_date)
        return {
            "dataset_name": result.dataset_name,
            "date_range": result.date_range,
            "peak_demand_periods": result.peak_demand_periods,
            "calculation_timestamp": result.calculation_timestamp
        }
    except Exception as e:
        logger.error(f"Error in peak demand analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in peak demand analysis: {str(e)}")








@app.get("/weather/summary", response_model=Dict[str, Any])
async def get_weather_summary(start_date: str = None, end_date: str = None):
    """
    Get weather summary analysis

    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = weather_analyzer.analyze_weather(start_date, end_date)
        return {
            "dataset_name": result.dataset_name,
            "date_range": result.date_range,
            "avg_temperature_celsius": result.avg_temperature_celsius,
            "avg_humidity_percent": result.avg_humidity_percent,
            "avg_wind_speed_mps": result.avg_wind_speed_mps,
            "avg_precipitation_mm": result.avg_precipitation_mm,
            "temperature_trends": result.temperature_trends,
            "precipitation_trends": result.precipitation_trends,
            "weather_patterns": result.weather_patterns,
            "seasonal_weather": result.seasonal_weather,
            "calculation_timestamp": result.calculation_timestamp
        }
    except Exception as e:
        logger.error(f"Error in weather summary analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in weather analysis: {str(e)}")





@app.get("/statistics", response_model=Dict[str, Any])
async def get_statistical_analysis(dataset: str, start_date: str = None, end_date: str = None):
    """
    Get statistical analysis for a dataset

    Args:
        dataset: Dataset name ('demand', 'generation', or 'weather')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = statistical_analyzer.analyze_statistics(dataset, start_date, end_date)
        return {
            "dataset_name": result.dataset_name,
            "date_range": result.date_range,
            "rolling_averages": result.rolling_averages,
            "percentage_changes": result.percentage_changes,
            "standard_deviations": result.standard_deviations,
            "interquartile_ranges": result.interquartile_ranges,
            "trends": result.trends,
            "outliers": result.outliers,
            "distribution_summary": result.distribution_summary,
            "calculation_timestamp": result.calculation_timestamp
        }
    except Exception as e:
        logger.error(f"Error in statistical analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in statistical analysis: {str(e)}")


@app.get("/report", response_model=Dict[str, Any])
async def get_analytical_report(report_type: str, start_date: str = None, end_date: str = None):
    """
    Get structured analytical report
    
    Args:
        report_type: Type of report ('demand', 'generation', 'weather')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        if report_type == 'demand':
            # Get demand analysis first
            demand_result = demand_analyzer.analyze_demand(start_date, end_date)
            # Generate report
            report = reporting_engine.generate_demand_report(
                demand_result.__dict__, start_date, end_date
            )
            return report.__dict__

        elif report_type == 'generation':
            # Get generation analysis first
            gen_result = generation_analyzer.analyze_generation(start_date, end_date)
            # Generate report
            report = reporting_engine.generate_generation_report(
                gen_result.__dict__, start_date, end_date
            )
            return report.__dict__

        elif report_type == 'weather':
            # Get weather analysis first
            weather_result = weather_analyzer.analyze_weather(start_date, end_date)
            # Generate report
            report = reporting_engine.generate_weather_report(
                weather_result.__dict__, start_date, end_date
            )
            return report.__dict__

        else:
            raise HTTPException(status_code=400, detail="Invalid report type")

    except Exception as e:
        logger.error(f"Error in analytical report generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in report generation: {str(e)}")


@app.get("/demand/peak", response_model=Dict[str, Any])
async def get_peak_demand_analysis(start_date: str = None, end_date: str = None):
    """
    Get comprehensive peak demand analysis
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = peak_demand_analyzer.analyze_peak_demand(start_date, end_date)
        # Convert to serializable dict
        return {
            "dataset_name": result.dataset_name,
            "date_range": result.date_range,
            "highest_recorded_demand_mw": result.highest_recorded_demand_mw,
            "lowest_recorded_demand_mw": result.lowest_recorded_demand_mw,
            "average_demand_mw": result.average_demand_mw,
            "median_demand_mw": result.median_demand_mw,
            "highest_demand_period": result.highest_demand_period,
            "lowest_demand_period": result.lowest_demand_period,
            "daily_peak_demands": result.daily_peak_demands,
            "weekly_peak_demands": result.weekly_peak_demands,
            "monthly_peak_demands": result.monthly_peak_demands,
            "peak_timing_analysis": result.peak_timing_analysis,
            "demand_variability": result.demand_variability,
            "historical_comparisons": result.historical_comparisons,
            "calculation_timestamp": result.calculation_timestamp
        }
    except Exception as e:
        logger.error(f"Error in peak demand analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in peak demand analysis: {str(e)}")


@app.get("/demand/historical", response_model=Dict[str, Any])
async def get_historical_demand_analysis(start_date: str = None, end_date: str = None):
    """
    Get comprehensive historical demand analysis
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = historical_demand_analyzer.analyze_historical_demand(start_date, end_date)
        # Convert to serializable dict
        return {
            "dataset_name": result["dataset_name"],
            "date_range": result["date_range"],
            "total_demand_mwh": result["total_demand_mwh"],
            "average_demand_mw": result["average_demand_mw"],
            "min_demand_mw": result["min_demand_mw"],
            "max_demand_mw": result["max_demand_mw"],
            "median_demand_mw": result["median_demand_mw"],
            "peak_demand_periods": result["peak_demand_periods"],
            "daily_profiles": result["daily_profiles"],
            "weekly_patterns": result["weekly_patterns"],
            "monthly_patterns": result["monthly_patterns"],
            "seasonal_patterns": result["seasonal_patterns"],
            "growth_rate": result["growth_rate"],
            "historical_comparisons": result["historical_comparisons"],
            "calculation_timestamp": result["calculation_timestamp"]
        }
    except Exception as e:
        logger.error(f"Error in historical demand analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in historical demand analysis: {str(e)}")


@app.get("/generation/mix", response_model=Dict[str, Any])
async def get_generation_mix_analysis(start_date: str = None, end_date: str = None):
    """
    Get comprehensive generation mix analysis
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = generation_mix_analyzer.analyze_generation_mix(start_date, end_date)
        # Convert to serializable dict
        return {
            "dataset_name": result["dataset_name"],
            "date_range": result["date_range"],
            "total_generation_mw": result["total_generation_mw"],
            "renewable_generation_mw": result["renewable_generation_mw"],
            "fossil_generation_mw": result["fossil_generation_mw"],
            "nuclear_generation_mw": result["nuclear_generation_mw"],
            "generation_mix": result["generation_mix"],
            "daily_trends": result["daily_trends"],
            "monthly_trends": result["monthly_trends"],
            "fuel_type_breakdown": result["fuel_type_breakdown"],
            "composition_over_time": result["composition_over_time"],
            "renewable_trends": result["renewable_trends"],
            "calculation_timestamp": result["calculation_timestamp"]
        }
    except Exception as e:
        logger.error(f"Error in generation mix analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in generation mix analysis: {str(e)}")


@app.get("/generation/renewables", response_model=Dict[str, Any])
async def get_renewable_penetration_analysis(start_date: str = None, end_date: str = None):
    """
    Get comprehensive renewable energy penetration analysis
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = renewable_penetration_analyzer.analyze_renewable_penetration(start_date, end_date)
        # Convert to serializable dict
        return {
            "dataset_name": result["dataset_name"],
            "date_range": result["date_range"],
            "renewable_generation_mw": result["renewable_generation_mw"],
            "total_generation_mw": result["total_generation_mw"],
            "renewable_share_percentage": result["renewable_share_percentage"],
            "renewable_trends": result["renewable_trends"],
            "seasonal_contribution": result["seasonal_contribution"],
            "peak_renewable_periods": result["peak_renewable_periods"],
            "renewable_by_source": result["renewable_by_source"],
            "penetration_over_time": result["penetration_over_time"],
            "calculation_timestamp": result["calculation_timestamp"]
        }
    except Exception as e:
        logger.error(f"Error in renewable penetration analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in renewable penetration analysis: {str(e)}")


@app.get("/weather-demand/correlation", response_model=Dict[str, Any])
async def get_weather_demand_correlation(start_date: str = None, end_date: str = None):
    """
    Get weather-demand correlation analysis
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = weather_correlation_analyzer.analyze_weather_demand_correlations(start_date, end_date)
        # Convert to serializable dict
        return {
            "dataset_names": result["dataset_names"],
            "date_range": result["date_range"],
            "pearson_correlation": result["pearson_correlation"],
            "spearman_correlation": result["spearman_correlation"],
            "sample_size": result["sample_size"],
            "correlation_strength": result["correlation_strength"],
            "key_findings": result["key_findings"],
            "calculation_timestamp": result["calculation_timestamp"]
        }
    except Exception as e:
        logger.error(f"Error in weather-demand correlation analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in correlation analysis: {str(e)}")


@app.get("/weather-demand/patterns", response_model=Dict[str, Any])
async def get_weather_demand_patterns(start_date: str = None, end_date: str = None):
    """
    Get weather-demand pattern analysis
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        result = weather_correlation_analyzer.analyze_weather_demand_patterns(start_date, end_date)
        # Convert to serializable dict
        return {
            "dataset_names": result["dataset_names"],
            "date_range": result["date_range"],
            "temperature_demand_relationship": result["temperature_demand_relationship"],
            "seasonal_patterns": result["seasonal_patterns"],
            "hourly_patterns": result["hourly_patterns"],
            "sample_size": result["sample_size"],
            "calculation_timestamp": result["calculation_timestamp"]
        }
    except Exception as e:
        logger.error(f"Error in weather-demand pattern analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in pattern analysis: {str(e)}")