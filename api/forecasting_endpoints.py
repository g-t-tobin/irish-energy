"""
Forecasting API endpoints for Irish Energy Analytics Data Platform
"""
from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
from loguru import logger

# Import forecasting modules
from src.forecasting.forecasting_service import ForecastingService
from src.forecasting.baselines import BaselineForecaster
from src.forecasting.training import MLForecastModel
from src.forecasting.evaluation import Backtester
from src.forecasting.models import ForecastResult, ModelEvaluationResult
from src.forecasting.data_access import ForecastingDataAccessor
from src.forecasting.features import FeatureEngineer
from src.forecasting.reporting import ForecastingReporter

# Initialize data accessor
data_accessor = ForecastingDataAccessor()

# Initialize forecasting service
forecasting_service = ForecastingService()

# Initialize other components
feature_engineer = FeatureEngineer()
baseline_forecaster = BaselineForecaster()
backtester = Backtester()
reporter = ForecastingReporter()

# Define the API routes for forecasting functionality
# Note: This will be mounted under /forecast in main.py
app = FastAPI(title="Forecasting API", version="1.0.0")


@app.get("/health", response_model=dict)
async def forecasting_health_check():
    """Health check endpoint for forecasting service"""
    return {"status": "healthy", "service": "forecasting"}


@app.get("/demand", response_model=Dict[str, Any])
async def get_demand_forecast(
    forecast_horizon: int = 1,
    forecast_method: str = "persistence",
    start_date: str = None,
    end_date: str = None
):
    """
    Get demand forecast using specified method

    Args:
        forecast_horizon: Number of days to forecast (default: 1)
        forecast_method: Method to use ('persistence', 'seasonal_naive', 'moving_average', 'statistical_baseline')
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    """
    try:
        # Get demand data
        data = data_accessor.get_demand_data(start_date, end_date)

        if data.empty:
            raise HTTPException(status_code=404, detail="No demand data available")

        # Generate forecast using specified method
        forecast = forecasting_service.generate_baseline_forecast(
            data,
            forecast_method,
            forecast_horizon
        )

        # Generate report
        report = reporter.generate_forecast_report(forecast)

        return report

    except Exception as e:
        logger.error(f"Error in demand forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in forecast: {str(e)}")


@app.get("/models", response_model=Dict[str, Any])
async def get_available_models():
    """
    Get list of available forecasting models
    """
    try:
        # For now, return a list of available methods
        available_models = {
            "baseline_methods": [
                "persistence",
                "seasonal_naive",
                "moving_average",
                "statistical_baseline"
            ],
            "ml_models": [
                "linear_regression",
                "random_forest",
                "gradient_boosting"
            ],
            "forecast_horizons": [
                1,  # 1 day
                7,  # 1 week
                30  # 1 month
            ]
        }

        return available_models

    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")


@app.get("/demand/evaluation", response_model=Dict[str, Any])
async def evaluate_forecast_models(
    model_type: str = "baseline",
    forecast_horizon: int = 1,
    start_date: str = None,
    end_date: str = None,
    test_period_start: str = None,
    test_period_end: str = None
):
    """
    Evaluate forecasting models

    Args:
        model_type: Type of models to evaluate ('baseline', 'linear_regression', 'random_forest', etc.)
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
        if model_type == "baseline":
            # Evaluate all baseline models
            results = baseline_forecaster.evaluate_baseline_models(
                data,
                test_period_start or "2023-01-01",
                test_period_end or "2023-12-31",
                forecast_horizon
            )

            # Generate evaluation report
            report = reporter.generate_evaluation_report(results)
            return report

        # For ML models
        elif model_type in ["linear_regression", "random_forest", "gradient_boosting"]:
            # This would normally involve training and evaluating actual ML models
            # For demo purposes, we'll return a placeholder response
            return {
                "message": f"Evaluation for {model_type} model",
                "status": "placeholder",
                "forecast_horizon": forecast_horizon
            }

        else:
            raise HTTPException(status_code=400, detail="Invalid model type")

    except Exception as e:
        logger.error(f"Error in forecast model evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in evaluation: {str(e)}")


@app.get("/backtesting", response_model=Dict[str, Any])
async def perform_backtesting(
    model_type: str = "linear_regression",
    train_window: int = 30,
    forecast_horizon: int = 1,
    test_size: int = 30,
    start_date: str = None,
    end_date: str = None
):
    """
    Perform backtesting for forecasting models

    Args:
        model_type: Type of model to test ('linear_regression', 'random_forest', etc.)
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
            "message": "Backtesting performed",
            "model_type": model_type,
            "train_window": train_window,
            "forecast_horizon": forecast_horizon,
            "test_size": test_size,
            "status": "demo_placeholder"
        }

    except Exception as e:
        logger.error(f"Error in backtesting: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in backtesting: {str(e)}")