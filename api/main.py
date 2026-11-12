from fastapi import FastAPI, Depends, HTTPException
from typing import List
from models.models_definitions import DataQualityMetrics, SummaryData
from models.frontend_compatibility import (
    FrontendDemandData, FrontendWeatherData, FrontendGenerationData,
    FrontendDataQualityMetrics, FrontendSummaryData,
    convert_api_to_frontend_demand, convert_api_to_frontend_weather,
    convert_api_to_frontend_generation, convert_api_to_frontend_quality,
    convert_api_to_frontend_summary
)
from src.services.data_service import (
    GoldDataAccessError, GoldDataNotFoundError, GoldDataParseError,
    GoldDataValidationError, S3GoldDataRetriever
)
from typing import Any

# Import observability endpoints
from observability_endpoints import app as observability_app

# Import alerting endpoints
from alerting_endpoints import app as alerting_app

# Import analytics endpoints
from analytics_endpoints import app as analytics_app

# Import forecasting endpoints
from forecasting_endpoints import app as forecasting_app

# Import renewable forecasting endpoints
from renewable_forecasting_endpoints import app as renewable_forecasting_app

app = FastAPI(title="Irish Energy Analytics API", version="1.0.0")

# Include observability endpoints
app.mount("/observability", observability_app)

# Include alerting endpoints
app.mount("/alerts", alerting_app)

# Include analytics endpoints
app.mount("/analytics", analytics_app)

# Include forecasting endpoints
app.mount("/forecast", forecasting_app)

# Include renewable forecasting endpoints
app.mount("/forecast/renewables", renewable_forecasting_app)

# Initialize data retriever
data_retriever = S3GoldDataRetriever()


def _gold_http_exception(exc: Exception, context: str) -> HTTPException:
    if isinstance(exc, GoldDataNotFoundError):
        return HTTPException(status_code=404, detail=f"{context}: {exc}")
    if isinstance(exc, GoldDataValidationError):
        return HTTPException(status_code=400, detail=f"{context}: {exc}")
    if isinstance(exc, GoldDataAccessError):
        return HTTPException(status_code=503, detail=f"{context}: {exc}")
    if isinstance(exc, GoldDataParseError):
        return HTTPException(status_code=500, detail=f"{context}: {exc}")
    return HTTPException(status_code=500, detail=f"{context}: {exc}")

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/demand", response_model=List[FrontendDemandData])
async def get_demand_data(start_date: str = None, end_date: str = None):
    """Retrieve demand data from Gold layer"""
    try:
        data = data_retriever.get_demand_data(start_date, end_date)
        return convert_api_to_frontend_demand(data)
    except Exception as e:
        raise _gold_http_exception(e, "Error retrieving demand data")

@app.get("/weather", response_model=List[FrontendWeatherData])
async def get_weather_data(start_date: str = None, end_date: str = None):
    """Retrieve weather data from Gold layer"""
    try:
        data = data_retriever.get_weather_data(start_date, end_date)
        return convert_api_to_frontend_weather(data)
    except Exception as e:
        raise _gold_http_exception(e, "Error retrieving weather data")

@app.get("/generation", response_model=List[FrontendGenerationData])
async def get_generation_data(start_date: str = None, end_date: str = None):
    """Retrieve generation data from Gold layer"""
    try:
        data = data_retriever.get_generation_data(start_date, end_date)
        return convert_api_to_frontend_generation(data)
    except Exception as e:
        raise _gold_http_exception(e, "Error retrieving generation data")

@app.get("/quality", response_model=List[FrontendDataQualityMetrics])
async def get_quality_metrics():
    """Retrieve data quality metrics from Gold layer"""
    try:
        data = data_retriever.get_quality_metrics()
        return convert_api_to_frontend_quality(data)
    except Exception as e:
        raise _gold_http_exception(e, "Error retrieving quality metrics")

@app.get("/summary", response_model=FrontendSummaryData)
async def get_summary_data():
    """Retrieve summary data about the Gold layer"""
    try:
        data = data_retriever.get_summary_data()
        return convert_api_to_frontend_summary(data)
    except Exception as e:
        raise _gold_http_exception(e, "Error retrieving summary data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)