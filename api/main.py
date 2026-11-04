from fastapi import FastAPI, Depends, HTTPException
from typing import List
from api.models import DemandData, WeatherData, GenerationData, DataQualityMetrics, SummaryData
from api.models.frontend_compatibility import (
    FrontendDemandData, FrontendWeatherData, FrontendGenerationData,
    FrontendDataQualityMetrics, FrontendSummaryData,
    convert_api_to_frontend_demand, convert_api_to_frontend_weather,
    convert_api_to_frontend_generation, convert_api_to_frontend_quality,
    convert_api_to_frontend_summary
)
from api.services.data_service import S3GoldDataRetriever

app = FastAPI(title="Irish Energy Analytics API", version="1.0.0")

# Initialize data retriever
data_retriever = S3GoldDataRetriever()

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/demand", response_model=List[FrontendDemandData])
async def get_demand_data(start_date: str = None, end_date: str = None):
    """Retrieve demand data from Gold layer"""
    try:
        data = data_retriever.get_demand_data(start_date, end_date)
        # Convert to proper format for response
        api_data = [DemandData(**item) for item in data]
        return convert_api_to_frontend_demand(api_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving demand data: {str(e)}")

@app.get("/weather", response_model=List[FrontendWeatherData])
async def get_weather_data(start_date: str = None, end_date: str = None):
    """Retrieve weather data from Gold layer"""
    try:
        data = data_retriever.get_weather_data(start_date, end_date)
        # Convert to proper format for response
        api_data = [WeatherData(**item) for item in data]
        return convert_api_to_frontend_weather(api_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving weather data: {str(e)}")

@app.get("/generation", response_model=List[FrontendGenerationData])
async def get_generation_data(start_date: str = None, end_date: str = None):
    """Retrieve generation data from Gold layer"""
    try:
        data = data_retriever.get_generation_data(start_date, end_date)
        # Convert to proper format for response
        api_data = [GenerationData(**item) for item in data]
        return convert_api_to_frontend_generation(api_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving generation data: {str(e)}")

@app.get("/quality", response_model=List[FrontendDataQualityMetrics])
async def get_quality_metrics():
    """Retrieve data quality metrics from Gold layer"""
    try:
        data = data_retriever.get_quality_metrics()
        # Convert to proper format for response
        api_data = [DataQualityMetrics(**item) for item in data]
        return convert_api_to_frontend_quality(api_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving quality metrics: {str(e)}")

@app.get("/summary", response_model=FrontendSummaryData)
async def get_summary_data():
    """Retrieve summary data about the Gold layer"""
    try:
        data = data_retriever.get_summary_data()
        api_data = SummaryData(**data)
        return convert_api_to_frontend_summary(api_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving summary data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)