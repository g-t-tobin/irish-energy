"""
Renewable energy forecasting API endpoints
"""

from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from loguru import logger

# Import renewable forecasting modules
from src.forecasting.renewable_service import RenewableForecastingService
from src.forecasting.wind_forecasting import WindForecaster
from src.forecasting.solar_forecasting import SolarForecaster
from src.forecasting.renewable_models import RenewableForecastResult
from src.forecasting.renewable_evaluation import RenewableBacktester
from src.forecasting.data_access import ForecastingDataAccessor
from src.forecasting.renewable_features import RenewableFeatureEngineer
from src.forecasting.reporting import ForecastingReporter

# Initialize data accessor
data_accessor = ForecastingDataAccessor()

# Initialize renewable forecasting service
renewable_forecasting_service = RenewableForecastingService()

# Initialize other components
feature_engineer = RenewableFeatureEngineer()
wind_forecaster = WindForecaster()
solar_forecaster = SolarForecaster()
backtester = RenewableBacktester()
reporter = ForecastingReporter()

# Define the API routes for renewable forecasting functionality
# Note: This will be mounted under /forecast/renewables in main.py
app = FastAPI(title="Renewable Forecasting API", version="1.0.0")


@app.get("/health", response_model=dict)
async def renewable_health_check():
    """Health check endpoint for renewable forecasting service"""
    return {"status": "healthy", "service": "renewable_forecasting"}


@app.get("/wind", response_model=Dict[str, Any])
async def get_wind_forecast(
    forecast_horizon: int = 1,
    forecast_method: str = "persistence",
    start_date: str = None,
    end_date: str = None
):
    """
    Get wind generation forecast

    Args:
        forecast_horizon: Number of days to forecast (default: 1)
        forecast_method: Method to use ('persistence', 'seasonal_naive', 'moving_average', 'statistical_baseline')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        # Get generation data
        data = data_accessor.get_generation_data(start_date, end_date)

        if data.empty:
            raise HTTPException(status_code=404, detail="No generation data available")

        # Generate wind forecast
        forecast = renewable_forecasting_service.generate_wind_forecast(
            data,
            forecast_horizon,
            forecast_method
        )

        # Generate report
        report = reporter.generate_forecast_report(forecast)

        return report

    except Exception as e:
        logger.error(f"Error in wind forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in wind forecast: {str(e)}")


@app.get("/solar", response_model=Dict[str, Any])
async def get_solar_forecast(
    forecast_horizon: int = 1,
    forecast_method: str = "persistence",
    start_date: str = None,
    end_date: str = None
):
    """
    Get solar generation forecast

    Args:
        forecast_horizon: Number of days to forecast (default: 1)
        forecast_method: Method to use ('persistence', 'seasonal_naive', 'moving_average', 'statistical_baseline')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        # Get generation data
        data = data_accessor.get_generation_data(start_date, end_date)

        if data.empty:
            raise HTTPException(status_code=404, detail="No generation data available")

        # Generate solar forecast (using renewable data as proxy)
        forecast = renewable_forecasting_service.generate_solar_forecast(
            data,
            forecast_horizon,
            forecast_method
        )

        # Generate report
        report = reporter.generate_forecast_report(forecast)

        return report

    except Exception as e:
        logger.error(f"Error in solar forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in solar forecast: {str(e)}")


@app.get("/renewables", response_model=Dict[str, Any])
async def get_renewable_total_forecast(
    forecast_horizon: int = 1,
    forecast_method: str = "persistence",
    start_date: str = None,
    end_date: str = None
):
    """
    Get total renewable generation forecast

    Args:
        forecast_horizon: Number of days to forecast (default: 1)
        forecast_method: Method to use ('persistence', 'seasonal_naive', 'moving_average', 'statistical_baseline')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        # Get generation data
        data = data_accessor.get_generation_data(start_date, end_date)

        if data.empty:
            raise HTTPException(status_code=404, detail="No generation data available")

        # Generate renewable total forecast
        forecast = renewable_forecasting_service.generate_renewable_total_forecast(
            data,
            forecast_horizon,
            forecast_method
        )

        # Generate report
        report = reporter.generate_forecast_report(forecast)

        return report

    except Exception as e:
        logger.error(f"Error in renewable forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in renewable forecast: {str(e)}")


@app.get("/models", response_model=Dict[str, Any])
async def get_available_renewable_models():
    """
    Get list of available renewable forecasting models
    """
    try:
        # Return available models for each category
        available_models = {
            "wind_models": [
                "persistence",
                "seasonal_naive",
                "moving_average",
                "statistical_baseline"
            ],
            "solar_models": [
                "persistence",
                "seasonal_naive",
                "moving_average",
                "statistical_baseline"
            ],
            "renewable_total_models": [
                "persistence",
                "seasonal_naive",
                "moving_average",
                "statistical_baseline"
            ],
            "forecast_horizons": [
                1,  # 1 day
                7,  # 1 week
                30  # 1 month
            ]
        }

        return available_models

    except Exception as e:
        logger.error(f"Error getting available renewable models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting renewable models: {str(e)}")


@app.get("/evaluation", response_model=Dict[str, Any])
async def evaluate_renewable_models(
    generation_category: str = "renewable_total",
    forecast_horizon: int = 1,
    start_date: str = None,
    end_date: str = None,
    test_period_start: str = None,
    test_period_end: str = None
):
    """
    Evaluate renewable forecasting models

    Args:
        generation_category: Type of generation ('wind', 'solar', 'renewable_total')
        forecast_horizon: Number of days to forecast
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        test_period_start: Start of test period in YYYY-MM-DD format (optional)
        test_period_end: End of test period in YYYY-MM-DD format (optional)
    """
    try:
        # Get data
        data = data_accessor.get_aligned_data(start_date, end_date)

        if data.empty:
            raise HTTPException(status_code=404, detail="No aligned data available")

        # For baseline models
        if generation_category == "wind":
            # Evaluate wind models
            results = wind_forecaster.evaluate_baseline_models(
                data,
                test_period_start or "2023-01-01",
                test_period_end or "2023-12-31",
                forecast_horizon
            )

            # Generate evaluation report
            report = reporter.generate_evaluation_report(results)
            return report

        elif generation_category == "solar":
            # Evaluate solar models
            results = solar_forecaster.evaluate_baseline_models(
                data,
                test_period_start or "2023-01-01",
                test_period_end or "2023-12-31",
                forecast_horizon
            )

            # Generate evaluation report
            report = reporter.generate_evaluation_report(results)
            return report

        elif generation_category == "renewable_total":
            # For renewable total, we can use baseline forecaster directly
            # This would normally involve training and evaluating actual ML models
            # For demo purposes, we'll return a placeholder response
            return {
                "message": f"Evaluation for {generation_category} model",
                "status": "placeholder",
                "forecast_horizon": forecast_horizon,
                "generation_category": generation_category
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid generation category")

    except Exception as e:
        logger.error(f"Error in renewable model evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in evaluation: {str(e)}")


@app.get("/demand-comparison", response_model=Dict[str, Any])
async def compare_renewable_with_demand(
    forecast_horizon: int = 1,
    start_date: str = None,
    end_date: str = None,
    demand_forecast_method: str = "persistence",
    renewable_forecast_method: str = "persistence"
):
    """
    Compare renewable generation forecast with demand forecast

    Args:
        forecast_horizon: Number of days to forecast
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        demand_forecast_method: Method for demand forecasting
        renewable_forecast_method: Method for renewable forecasting
    """
    try:
        # Get demand data
        demand_data = data_accessor.get_demand_data(start_date, end_date)

        # Get generation data
        generation_data = data_accessor.get_generation_data(start_date, end_date)

        if demand_data.empty or generation_data.empty:
            raise HTTPException(status_code=404, detail="No data available for comparison")

        # Generate forecasts for both
        demand_forecast = renewable_forecasting_service.generate_renewable_total_forecast(
            demand_data,
            forecast_horizon,
            demand_forecast_method
        )

        renewable_forecast = renewable_forecasting_service.generate_renewable_total_forecast(
            generation_data,
            forecast_horizon,
            renewable_forecast_method
        )

        # Create comparison report
        comparison = {
            "forecast_timestamp": datetime.now().isoformat(),
            "forecast_horizon_days": forecast_horizon,
            "demand_forecast": {
                "predicted_demand_mw": demand_forecast.predicted_generation_mw,
                "model_identifier": demand_forecast.model_identifier,
                "generation_category": demand_forecast.generation_category
            },
            "renewable_forecast": {
                "predicted_generation_mw": renewable_forecast.predicted_generation_mw,
                "model_identifier": renewable_forecast.model_identifier,
                "generation_category": renewable_forecast.generation_category
            },
            "renewable_as_percentage_of_demand": (
                renewable_forecast.predicted_generation_mw / demand_forecast.predicted_generation_mw * 100
                if demand_forecast.predicted_generation_mw > 0 else 0
            ) if demand_forecast.predicted_generation_mw > 0 else 0,
            "difference": (
                demand_forecast.predicted_generation_mw - renewable_forecast.predicted_generation_mw
            ),
            "notes": "This is a simplified comparison. Actual system adequacy requires considering other generation sources, storage, imports, exports, network constraints and operational reserves."
        }

        return comparison

    except Exception as e:
        logger.error(f"Error in demand comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in demand comparison: {str(e)}")


@app.get("/backtesting", response_model=Dict[str, Any])
async def perform_renewable_backtesting(
    generation_category: str = "renewable_total",
    train_window: int = 30,
    forecast_horizon: int = 1,
    test_size: int = 30,
    start_date: str = None,
    end_date: str = None
):
    """
    Perform backtesting for renewable forecasting models

    Args:
        generation_category: Type of generation ('wind', 'solar', 'renewable_total')
        train_window: Size of training window in days
        forecast_horizon: Forecast horizon in days
        test_size: Number of test periods
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        # Get data
        data = data_accessor.get_aligned_data(start_date, end_date)

        if data.empty:
            raise HTTPException(status_code=404, detail="No aligned data available")

        # For demo purposes, return a placeholder response
        # In a real implementation, this would perform actual backtesting
        return {
            "message": "Renewable backtesting performed",
            "generation_category": generation_category,
            "train_window": train_window,
            "forecast_horizon": forecast_horizon,
            "test_size": test_size,
            "status": "demo_placeholder"
        }

    except Exception as e:
        logger.error(f"Error in renewable backtesting: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in renewable backtesting: {str(e)}")